"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import json
import os
import re
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from .task9_retrieval_pipeline import retrieve_with_trace
from .pipeline_observability import ProgressCallback, new_request_id, record_event, safe_error


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý tra cứu tuyển sinh. Chỉ sử dụng Context được cung cấp.
Mỗi thông tin thực tế phải gắn citation dạng [chunk_id] với đúng ID trong Context.
Nếu Context không đủ để trả lời, hãy nói không thể xác minh từ nguồn hiện có.
Không tạo URL, quy định hoặc mốc thời gian không có trong Context."""
SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn tuyển sinh hiện có."


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    return list(chunks[::2]) + list(reversed(chunks[1::2]))


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        parts.append(
            f"[ID: {chunk['id']} | Title: {metadata['title']} | "
            f"Source: {metadata['source']} | URL: {metadata.get('url') or 'không có'}]\n"
            f"{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def _post_json(url: str, headers: dict[str, str], payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    model = os.getenv("LLM_MODEL", LLM_MODEL)
    if not model:
        raise RuntimeError("LLM_MODEL chưa được cấu hình")
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình")
        response = _post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": key},
            {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                "generationConfig": {"temperature": TEMPERATURE, "topP": TOP_P},
            },
        )
        return "".join(
            part.get("text", "") for candidate in response.get("candidates", [])[:1]
            for part in candidate.get("content", {}).get("parts", [])
        ).strip()
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình")
        response = _post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}"},
            {"model": model, "temperature": TEMPERATURE,
             "messages": [{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_message}]},
        )
        return response["choices"][0]["message"]["content"].strip()
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY chưa được cấu hình")
        response = _post_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {"model": model, "max_tokens": 1024, "system": system_prompt,
             "messages": [{"role": "user", "content": user_message}]},
        )
        return "".join(part.get("text", "") for part in response.get("content", [])).strip()
    raise RuntimeError(f"LLM_PROVIDER không hỗ trợ: {provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    result, _ = generate_with_trace(query, top_k)
    return result


def generate_with_trace(
    query: str, top_k: int = TOP_K, on_step: ProgressCallback | None = None,
) -> tuple[dict, dict]:
    """Generate an answer and return the exact retrieval trace used for it."""
    chunks, trace = retrieve_with_trace(query, top_k=top_k, on_step=on_step)
    events = trace.setdefault("events", [])
    request_id = trace.setdefault("request_id", new_request_id())

    def emit(stage: str, status: str, message: str, **details) -> None:
        record_event(events, request_id, stage, status, message, on_step, **details)

    refusal = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    if not chunks or (
        trace.get("fallback_attempted") and trace.get("decision") != "pageindex"
    ):
        trace["generation_status"] = "no_evidence"
        emit("generation", "skipped", "Không đủ bằng chứng để gọi LLM", count=len(chunks))
        return refusal, trace

    trace["context_chunks"] = reorder_for_llm(chunks)
    emit("context", "completed", "Đã chuẩn bị các đoạn tài liệu cho LLM", count=len(chunks))
    result = answer_from_chunks(
        query, chunks, on_step=on_step, events=events, request_id=request_id,
    )
    trace["generation_status"] = "cited" if result["sources"] else "refused"
    return result, trace


def answer_from_chunks(
    query: str, chunks: list[dict], *, on_step: ProgressCallback | None = None,
    events: list[dict] | None = None, request_id: str | None = None,
) -> dict:
    """Use one generation policy for live chat and the A/B experiment."""
    if events is None:
        events = []
    if request_id is None:
        request_id = new_request_id()

    def emit(status: str, message: str, **details) -> None:
        record_event(events, request_id, "generation", status, message, on_step, **details)

    refusal = {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    if not chunks:
        emit("skipped", "Không có context để tạo câu trả lời")
        return refusal
    context = format_context(reorder_for_llm(chunks))
    emit("started", "Đang gọi LLM để tạo câu trả lời", context_count=len(chunks))
    try:
        answer = call_llm(SYSTEM_PROMPT, f"Context:\n{context}\n\nQuestion: {query}")
    except Exception as error:
        emit("error", "LLM lỗi; trả lời an toàn", error=safe_error(error))
        return refusal

    raw_citations = re.findall(r"\[([^\]\n]+)\]", answer)
    cited_ids = set()
    for citation in raw_citations:
        for item in re.split(r"[,;]\s*", citation):
            item = item.strip()
            if item:
                cited_ids.add(item)
    source_ids = {chunk["id"] for chunk in chunks}
    if not answer or not cited_ids or not cited_ids <= source_ids:
        emit("refused", "LLM không trả citation hợp lệ", cited_count=len(cited_ids))
        return refusal
    method = chunks[0]["retrieval_method"]
    retrieval_source = "pageindex" if method == "pageindex" else "hybrid"
    cited_sources = [chunk for chunk in chunks if chunk["id"] in cited_ids]
    emit("completed", "Đã xác minh citation trong câu trả lời", source_count=len(cited_sources))
    return {"answer": answer, "sources": cited_sources, "retrieval_source": retrieval_source}


if __name__ == "__main__":
    print(generate_with_citation("test query"))

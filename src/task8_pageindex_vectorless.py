"""Optional PageIndex cloud fallback over the collected policy PDFs.

Only cited pages become SearchResults. A provider answer without retrievable
page text is not evidence and is never passed to generation.
"""

import hashlib
import json
import os
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False


load_dotenv()
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
LEGAL_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
CACHE_PATH = Path(__file__).parent.parent / ".cache" / "pageindex_documents.json"
PAGEINDEX_TIMEOUT_SECONDS = 25


def _new_client():
    from pageindex import PageIndexClient

    model = os.getenv("PAGEINDEX_CHAT_MODEL") or os.getenv("LLM_MODEL")
    if not model:
        raise RuntimeError("PAGEINDEX_CHAT_MODEL hoặc LLM_MODEL chưa được cấu hình")
    return PageIndexClient(index="cloud", chat=model, api_key=PAGEINDEX_API_KEY)


def _fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upload_documents(client=None) -> dict[str, str]:
    """Return filename -> document ID, uploading changed PDFs only once."""
    if not PAGEINDEX_API_KEY:
        return {}
    pdfs = sorted(LEGAL_DIR.glob("*.pdf"))
    if not pdfs:
        return {}
    client = client or _new_client()
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        cache = {}

    current = {}
    for path in pdfs:
        digest = _fingerprint(path)
        cached = cache.get(path.name, {})
        if cached.get("sha256") == digest and cached.get("doc_id"):
            doc_id = cached["doc_id"]
        else:
            doc_id = client.submit_document(str(path), wait=True)["doc_id"]
        current[path.name] = {"sha256": digest, "doc_id": doc_id}
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return {name: row["doc_id"] for name, row in current.items()}


def _search(query: str, top_k: int) -> list[dict]:
    client = _new_client()
    ids_by_name = upload_documents(client)
    if not ids_by_name:
        return []
    answer = client.chat(query, doc_id=list(ids_by_name.values()), citations=True)
    citations = client.get_citations(answer)
    results = []
    seen = set()
    for citation in citations:
        doc_id = citation.get("doc_id") or ids_by_name.get(citation.get("document"))
        page = citation.get("page")
        source = citation.get("document") or next(
            (name for name, value in ids_by_name.items() if value == doc_id), None
        )
        if not doc_id or not source or not isinstance(page, int):
            continue
        item_id = f"pageindex::{doc_id}::page-{page}"
        if item_id in seen:
            continue
        pages = client.get_page_content(doc_id, str(page))
        content = "\n".join(row.get("markdown", "") for row in pages).strip()
        if not content:
            continue
        seen.add(item_id)
        results.append({
            "id": item_id,
            "content": content,
            "score": 1.0 / (len(results) + 1),
            "metadata": {
                "source": source,
                "title": Path(source).stem,
                "doc_type": "legal",
                "url": None,
                "chunk_index": max(page - 1, 0),
                "page": page,
            },
            "retrieval_method": "pageindex",
        })
        if len(results) >= top_k:
            break
    return results


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Search PageIndex with a deadline; missing configuration yields no result."""
    if not PAGEINDEX_API_KEY or top_k <= 0:
        return []
    outcome: Queue = Queue(maxsize=1)

    def run() -> None:
        try:
            outcome.put((True, _search(query, top_k)))
        except Exception as error:
            outcome.put((False, error))

    Thread(target=run, daemon=True).start()
    try:
        success, value = outcome.get(timeout=PAGEINDEX_TIMEOUT_SECONDS)
    except Empty as error:
        raise TimeoutError("PageIndex quá thời gian chờ") from error
    if not success:
        raise value
    return value


if __name__ == "__main__":
    print(upload_documents())

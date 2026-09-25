"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

import os
from time import perf_counter

from .pipeline_observability import ProgressCallback, new_request_id, record_event, safe_error
from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


try:
    SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or "0.3")
except ValueError:
    SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    results, _ = retrieve_with_trace(query, top_k, score_threshold, use_reranking)
    return results


def retrieve_with_trace(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
    on_step: ProgressCallback | None = None,
) -> tuple[list[dict], dict]:
    """Run retrieval once and retain each stage for the explainer UI."""
    request_id = new_request_id()
    events: list[dict] = []

    def emit(stage: str, status: str, message: str, **details) -> None:
        record_event(events, request_id, stage, status, message, on_step, **details)

    emit("request", "started", "Bắt đầu truy xuất", top_k=top_k)
    if top_k <= 0:
        emit("request", "completed", "Không có kết quả vì top_k không hợp lệ", count=0)
        return [], {
            "dense": [], "bm25": [], "hybrid": [], "final": [],
            "best_dense_score": 0.0, "score_threshold": score_threshold,
            "decision": "no_results", "fallback_attempted": False,
            "request_id": request_id, "events": events,
        }

    started = perf_counter()
    emit("dense", "started", "Đang tìm theo ngữ nghĩa")
    try:
        dense = semantic_search(query, top_k=top_k * 2)
    except Exception as error:
        emit("dense", "error", "Dense search lỗi", error=safe_error(error))
        raise
    emit("dense", "completed", "Dense search hoàn tất", count=len(dense),
         elapsed_ms=round((perf_counter() - started) * 1000))

    bm25 = []
    if use_reranking:
        started = perf_counter()
        emit("bm25", "started", "Đang tìm theo từ khóa")
        try:
            bm25 = lexical_search(query, top_k=top_k * 2)
        except Exception as error:
            emit("bm25", "error", "BM25 search lỗi", error=safe_error(error))
            raise
        emit("bm25", "completed", "BM25 search hoàn tất", count=len(bm25),
             elapsed_ms=round((perf_counter() - started) * 1000))

    started = perf_counter()
    emit("rrf", "started", "Đang gộp thứ hạng")
    try:
        hybrid = rerank_rrf([dense, bm25], top_k=top_k) if use_reranking else dense[:top_k]
    except Exception as error:
        emit("rrf", "error", "Gộp thứ hạng lỗi", error=safe_error(error))
        raise
    emit("rrf", "completed", "Gộp thứ hạng hoàn tất", count=len(hybrid),
         elapsed_ms=round((perf_counter() - started) * 1000))
    best_dense_score = max((row["score"] for row in dense), default=0.0)
    final = hybrid
    decision = "hybrid" if use_reranking else "dense"
    fallback_attempted = best_dense_score < score_threshold
    emit("fallback", "decision", "Đã so sánh cosine gốc với ngưỡng",
         best_dense_score=round(best_dense_score, 4),
         score_threshold=score_threshold, attempted=fallback_attempted)
    if fallback_attempted:
        started = perf_counter()
        emit("fallback", "started", "Đang thử PageIndex")
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                final = fallback[:top_k]
                decision = "pageindex"
            else:
                decision = "hybrid_after_empty_fallback" if use_reranking else "dense_after_empty_fallback"
            emit("fallback", "completed", "PageIndex đã phản hồi", count=len(fallback),
                 elapsed_ms=round((perf_counter() - started) * 1000))
        except Exception as error:
            decision = "hybrid_after_fallback_error" if use_reranking else "dense_after_fallback_error"
            emit("fallback", "error", "PageIndex lỗi; giữ kết quả hiện có",
                 error=safe_error(error), elapsed_ms=round((perf_counter() - started) * 1000))

    emit("request", "completed", "Truy xuất hoàn tất", count=len(final), decision=decision)

    trace = {
        "dense": dense, "bm25": bm25, "hybrid": hybrid,
        "final": final, "best_dense_score": best_dense_score,
        "score_threshold": score_threshold, "decision": decision,
        "fallback_attempted": fallback_attempted,
        "request_id": request_id, "events": events,
    }
    return final, trace


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)

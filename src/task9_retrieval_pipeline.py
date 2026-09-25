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
) -> tuple[list[dict], dict]:
    """Run retrieval once and retain each stage for the explainer UI."""
    if top_k <= 0:
        return [], {
            "dense": [], "bm25": [], "hybrid": [], "final": [],
            "best_dense_score": 0.0, "score_threshold": score_threshold,
            "decision": "no_results", "fallback_attempted": False,
        }

    dense = semantic_search(query, top_k=top_k * 2)
    bm25 = lexical_search(query, top_k=top_k * 2) if use_reranking else []
    hybrid = rerank_rrf([dense, bm25], top_k=top_k) if use_reranking else dense[:top_k]
    best_dense_score = max((row["score"] for row in dense), default=0.0)
    final = hybrid
    decision = "hybrid" if use_reranking else "dense"
    fallback_attempted = best_dense_score < score_threshold
    if fallback_attempted:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                final = fallback[:top_k]
                decision = "pageindex"
            else:
                decision = "hybrid_after_empty_fallback" if use_reranking else "dense_after_empty_fallback"
        except Exception:
            decision = "hybrid_after_fallback_error" if use_reranking else "dense_after_fallback_error"

    trace = {
        "dense": dense, "bm25": bm25, "hybrid": hybrid,
        "final": final, "best_dense_score": best_dense_score,
        "score_threshold": score_threshold, "decision": decision,
        "fallback_attempted": fallback_attempted,
    }
    return final, trace


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)

"""Pure formatting helpers for the Streamlit retrieval explainer."""


def search_rows(results: list[dict]) -> list[dict]:
    return [
        {
            "Hạng": rank,
            "Tài liệu": row["metadata"]["title"],
            "Chunk": row["id"],
            "Điểm": round(float(row["score"]), 4),
            "Đoạn trích": row["content"][:180],
        }
        for rank, row in enumerate(results, 1)
    ]


def fusion_rows(trace: dict) -> list[dict]:
    dense_rank = {row["id"]: rank for rank, row in enumerate(trace.get("dense", []), 1)}
    bm25_rank = {row["id"]: rank for rank, row in enumerate(trace.get("bm25", []), 1)}
    return [
        {
            "Hạng RRF": rank,
            "Tài liệu": row["metadata"]["title"],
            "Chunk": row["id"],
            "Hạng Dense": dense_rank.get(row["id"]),
            "Hạng BM25": bm25_rank.get(row["id"]),
            "Điểm RRF": float(row["score"]),
        }
        for rank, row in enumerate(trace.get("hybrid", []), 1)
    ]

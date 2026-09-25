"""Focused, dependency-free checks for the explainable RAG flow."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch


def item(item_id, score, method="dense"):
    return {
        "id": item_id,
        "content": f"Nội dung {item_id}",
        "score": score,
        "metadata": {
            "source": f"{item_id}.md",
            "title": f"Tài liệu {item_id}",
            "doc_type": "legal",
            "url": f"https://example.edu/{item_id}",
            "chunk_index": 0,
        },
        "retrieval_method": method,
    }


class RRFTests(unittest.TestCase):
    def test_rrf_explains_rank_and_does_not_mutate_inputs(self):
        from src.task7_reranking import rerank_rrf

        dense = [item("a", 0.9), item("b", 0.7)]
        sparse = [item("b", 12, "bm25"), item("c", 8, "bm25")]
        result = rerank_rrf([dense, sparse], top_k=3)
        self.assertEqual([row["id"] for row in result], ["b", "a", "c"])
        self.assertAlmostEqual(result[0]["score"], 1 / 62 + 1 / 61)
        self.assertEqual(result[0]["retrieval_method"], "hybrid")
        self.assertEqual(dense[1]["score"], 0.7)
        self.assertEqual(sparse[0]["retrieval_method"], "bm25")


class RetrievalTraceTests(unittest.TestCase):
    def test_trace_uses_one_search_per_method_and_original_dense_score(self):
        from src import task9_retrieval_pipeline as pipeline

        dense = [item("a", 0.2)]
        sparse = [item("b", 5, "bm25")]
        fallback = [item("c", 1, "pageindex")]
        with (
            patch.object(pipeline, "semantic_search", return_value=dense) as dense_call,
            patch.object(pipeline, "lexical_search", return_value=sparse) as bm25_call,
            patch.object(pipeline, "pageindex_search", return_value=fallback) as page_call,
        ):
            results, trace = pipeline.retrieve_with_trace("học bổng", top_k=2, score_threshold=0.4)
        self.assertEqual(results, fallback)
        self.assertEqual(trace["best_dense_score"], 0.2)
        self.assertEqual(trace["decision"], "pageindex")
        self.assertEqual(trace["dense"], dense)
        self.assertEqual(trace["bm25"], sparse)
        self.assertEqual(trace["final"], fallback)
        dense_call.assert_called_once()
        bm25_call.assert_called_once()
        page_call.assert_called_once()

    def test_fallback_error_keeps_hybrid_and_records_reason(self):
        from src import task9_retrieval_pipeline as pipeline

        with (
            patch.object(pipeline, "semantic_search", return_value=[item("a", 0.2)]),
            patch.object(pipeline, "lexical_search", return_value=[]),
            patch.object(pipeline, "pageindex_search", side_effect=RuntimeError("offline")),
        ):
            results, trace = pipeline.retrieve_with_trace("x", score_threshold=0.4)
        self.assertEqual(results[0]["retrieval_method"], "hybrid")
        self.assertEqual(trace["decision"], "hybrid_after_fallback_error")


class PageIndexTests(unittest.TestCase):
    def test_missing_key_returns_no_fallback(self):
        from src import task8_pageindex_vectorless as pageindex

        with patch.object(pageindex, "PAGEINDEX_API_KEY", ""):
            self.assertEqual(pageindex.pageindex_search("query"), [])

    def test_cited_pages_become_search_results(self):
        from src import task8_pageindex_vectorless as pageindex

        class FakeClient:
            def submit_document(self, path, wait=True):
                return {"doc_id": "doc-1"}

            def chat(self, query, doc_id, citations=True):
                return 'Nội dung <cite doc="policy.pdf" page="2"/>'

            def get_citations(self, answer):
                return [{"doc_id": "doc-1", "document": "policy.pdf", "page": 2}]

            def get_page_content(self, doc_id, page):
                return [{"page_index": 2, "markdown": "Điều kiện xét tuyển đã công bố."}]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legal = root / "legal"
            legal.mkdir()
            (legal / "policy.pdf").write_bytes(b"%PDF-1.4 test")
            with (
                patch.object(pageindex, "PAGEINDEX_API_KEY", "key"),
                patch.object(pageindex, "LEGAL_DIR", legal),
                patch.object(pageindex, "CACHE_PATH", root / "cache.json"),
                patch.object(pageindex, "_new_client", return_value=FakeClient()),
            ):
                results = pageindex.pageindex_search("điều kiện", top_k=2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["retrieval_method"], "pageindex")
        self.assertEqual(results[0]["content"], "Điều kiện xét tuyển đã công bố.")
        self.assertEqual(results[0]["metadata"]["source"], "policy.pdf")


class GenerationTests(unittest.TestCase):
    def test_generation_uses_same_trace_and_rejects_uncited_answer(self):
        from src import task10_generation as generation

        source = item("a", 0.03, "hybrid")
        trace = {"dense": [], "bm25": [], "hybrid": [source], "final": [source]}
        with (
            patch.object(generation, "retrieve_with_trace", return_value=([source], trace)),
            patch.object(generation, "call_llm", return_value="Một câu trả lời thiếu nguồn"),
        ):
            result, observed = generation.generate_with_trace("hỏi", top_k=1)
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["retrieval_source"], "none")
        self.assertIs(observed, trace)

    def test_cited_answer_maps_to_existing_chunk_id(self):
        from src import task10_generation as generation

        source = item("a", 0.03, "hybrid")
        with (
            patch.object(generation, "retrieve_with_trace", return_value=([source], {"final": [source]})),
            patch.object(generation, "call_llm", return_value="Theo tài liệu, cần nộp hồ sơ [a]."),
        ):
            result, _ = generation.generate_with_trace("hỏi", top_k=1)
        self.assertEqual(result["retrieval_source"], "hybrid")
        self.assertEqual(result["sources"], [source])

    def test_sources_contain_only_chunks_cited_by_answer(self):
        from src import task10_generation as generation

        cited = item("a", 0.04, "hybrid")
        uncited = item("b", 0.03, "hybrid")
        with (
            patch.object(generation, "retrieve_with_trace", return_value=([cited, uncited], {"final": [cited, uncited]})),
            patch.object(generation, "call_llm", return_value="Điều kiện được quy định [a]."),
        ):
            result, trace = generation.generate_with_trace("hỏi", top_k=2)
        self.assertEqual(result["sources"], [cited])
        self.assertEqual(len(trace["context_chunks"]), 2)


class PresentationTests(unittest.TestCase):
    def test_fusion_table_explains_both_rankings_and_rrf_score(self):
        from src.trace_presentation import fusion_rows

        dense = [item("a", 0.9), item("b", 0.8)]
        bm25 = [item("b", 7, "bm25"), item("c", 5, "bm25")]
        rows = fusion_rows({
            "dense": dense,
            "bm25": bm25,
            "hybrid": [item("b", 1 / 62 + 1 / 61, "hybrid")],
        })
        self.assertEqual(rows[0]["Chunk"], "b")
        self.assertEqual(rows[0]["Hạng Dense"], 2)
        self.assertEqual(rows[0]["Hạng BM25"], 1)
        self.assertAlmostEqual(rows[0]["Điểm RRF"], 1 / 62 + 1 / 61)


class EvaluationTests(unittest.TestCase):
    def test_empty_golden_file_reports_missing_cases(self):
        from src import evaluate_ab

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "golden.json"
            path.write_text("", encoding="utf-8")
            with patch.object(evaluate_ab, "GOLDEN_PATH", path):
                with self.assertRaisesRegex(ValueError, "ít nhất 15"):
                    evaluate_ab.main()

    def test_ab_disables_fallback_in_both_configs(self):
        from src import evaluate_ab

        golden = [{
            "question": "Điều kiện?",
            "expected_answer": "Theo quy chế tuyển sinh.",
            "expected_context": "Quy chế tuyển sinh",
        }]
        source = item("a", 0.8, "dense")
        with (
            patch.object(evaluate_ab, "retrieve", return_value=[source]) as retrieval,
            patch.object(evaluate_ab, "answer_from_chunks", return_value={
                "answer": "Theo quy chế tuyển sinh [a].", "sources": [source],
                "retrieval_source": "hybrid",
            }),
            patch.object(evaluate_ab, "judge_scores", return_value={
                "faithfulness": 1.0, "answer_relevance": 1.0,
                "context_recall": 1.0, "context_precision": 1.0,
            }),
        ):
            payload = evaluate_ab.run_evaluation(golden, top_k=3)
        self.assertEqual(len(payload["cases"]), 2)
        self.assertEqual([call.kwargs["use_reranking"] for call in retrieval.call_args_list], [False, True])
        self.assertTrue(all(call.kwargs["score_threshold"] == 0 for call in retrieval.call_args_list))
        self.assertEqual(payload["summary"]["B"]["faithfulness"], 1.0)


if __name__ == "__main__":
    unittest.main()

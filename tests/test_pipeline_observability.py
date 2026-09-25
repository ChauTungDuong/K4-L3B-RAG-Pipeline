"""Progress events must explain retrieval without leaking queries or keys."""

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from src import pipeline_observability as observability
from src import task9_retrieval_pipeline as pipeline
from src import task10_generation as generation


def result(item_id: str, method: str) -> dict:
    return {
        "id": item_id, "content": "Tài liệu tuyển sinh", "score": 0.8,
        "metadata": {"source": "source.md", "title": "Source", "doc_type": "legal",
                     "url": None, "chunk_index": 0},
        "retrieval_method": method,
    }


class ProgressTests(unittest.TestCase):
    def test_retrieval_reports_each_stage_and_preserves_trace(self):
        observed = []
        with (
            patch.object(pipeline, "semantic_search", return_value=[result("a", "dense")]),
            patch.object(pipeline, "lexical_search", return_value=[result("a", "bm25")]),
        ):
            rows, trace = pipeline.retrieve_with_trace(
                "private query", top_k=1, score_threshold=0, on_step=observed.append,
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(trace["events"], observed)
        self.assertEqual(
            [event["stage"] for event in observed if event["status"] == "completed"],
            ["dense", "bm25", "rrf", "request"],
        )
        self.assertNotIn("private query", json.dumps(observed))

    def test_file_log_redacts_http_error_details(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = logging.Logger("rag_demo_test")
            with (
                patch.object(observability, "LOG_PATH", Path(directory) / "rag_demo.log"),
                patch.object(observability, "_logger", logger),
            ):
                error = HTTPError("https://example.com?key=secret-value", 429, "quota", {}, None)
                events = []
                observability.record_event(
                    events, "abc123", "generation", "error", "LLM lỗi",
                    error=observability.safe_error(error),
                )
                saved = observability.LOG_PATH.read_text(encoding="utf-8")
                self.assertIn("HTTP 429", saved)
                self.assertNotIn("secret-value", saved)
                self.assertEqual(observability.recent_events(), events)
                error.close()
                for handler in logger.handlers:
                    handler.close()

    def test_generation_reports_http_error_before_safe_refusal(self):
        error = HTTPError("https://example.com?key=secret-value", 429, "quota", {}, None)
        events = []
        with patch.object(generation, "call_llm", side_effect=error):
            output = generation.answer_from_chunks(
                "question", [result("a", "dense")], on_step=events.append,
            )
        self.assertEqual(output["answer"], generation.SAFE_REFUSAL)
        self.assertEqual(events[-1]["status"], "error")
        self.assertEqual(events[-1]["error"], "HTTPError (HTTP 429)")
        self.assertNotIn("secret-value", json.dumps(events))
        error.close()


if __name__ == "__main__":
    unittest.main()

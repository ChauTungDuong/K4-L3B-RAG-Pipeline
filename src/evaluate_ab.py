"""Run a controlled dense-only versus Hybrid + RRF evaluation.

This writes measured case-level results. It does not invent scores when the
corpus, LLM or evaluator is unavailable.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from time import perf_counter

from .task9_retrieval_pipeline import retrieve
from .task10_generation import answer_from_chunks, call_llm


METRICS = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
ROOT = Path(__file__).parent.parent
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / "group_project" / "evaluation" / "results.json"


def judge_scores(question: str, expected_answer: str, expected_context: str,
                 answer: str, contexts: list[str]) -> dict[str, float]:
    """Ask one fixed evaluator rubric for four scores in [0, 1]."""
    prompt = (
        "Chấm bốn tiêu chí từ 0 đến 1, chỉ trả JSON object với đúng các khóa: "
        "faithfulness, answer_relevance, context_recall, context_precision. "
        "Faithfulness: mọi khẳng định trong answer được context hỗ trợ. "
        "Answer relevance: answer giải quyết question. "
        "Context recall: context chứa bằng chứng cần để trả expected_answer. "
        "Context precision: tỷ lệ context liên quan trực tiếp đến question. "
        "Không suy đoán thông tin ngoài input."
    )
    sample = json.dumps({
        "question": question, "expected_answer": expected_answer,
        "expected_context": expected_context, "answer": answer,
        "retrieved_contexts": contexts,
    }, ensure_ascii=False)
    raw = call_llm(prompt, sample).strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    scores = json.loads(raw)
    if set(scores) != set(METRICS):
        raise ValueError("Evaluator trả thiếu hoặc thừa metric")
    result = {name: float(scores[name]) for name in METRICS}
    if any(not 0 <= value <= 1 for value in result.values()):
        raise ValueError("Evaluator score phải nằm trong [0, 1]")
    return result


def run_evaluation(golden: list[dict], top_k: int = 5) -> dict:
    """Keep all settings fixed except retrieval strategy."""
    if not golden:
        raise ValueError("Golden dataset rỗng")
    cases = []
    for item in golden:
        for config, use_reranking in (("A", False), ("B", True)):
            start = perf_counter()
            chunks = retrieve(
                item["question"], top_k=top_k,
                score_threshold=0, use_reranking=use_reranking,
            )
            result = answer_from_chunks(item["question"], chunks)
            latency_seconds = perf_counter() - start
            scores = judge_scores(
                item["question"], item["expected_answer"],
                item["expected_context"], result["answer"],
                [row["content"] for row in chunks],
            )
            cases.append({
                "config": config, "question": item["question"],
                "expected_answer": item["expected_answer"],
                "expected_context": item["expected_context"],
                "answer": result["answer"],
                "source_ids": [row["id"] for row in chunks],
                "retrieved_contexts": [row["content"] for row in chunks],
                "latency_seconds": round(latency_seconds, 3),
                **scores,
            })
    summary = {
        config: {
            **{name: mean(row[name] for row in cases if row["config"] == config)
               for name in METRICS},
            "latency_seconds": mean(row["latency_seconds"] for row in cases if row["config"] == config),
        }
        for config in ("A", "B")
    }
    try:
        corpus_version = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        corpus_version = "unversioned"
    return {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "corpus_version": corpus_version,
        "generator_provider": os.getenv("LLM_PROVIDER", "openai"),
        "generator_model": os.getenv("LLM_MODEL", ""),
        "evaluator_model": os.getenv("LLM_MODEL", ""),
        "top_k": top_k,
        "fallback_threshold": 0,
        "golden_size": len(golden),
        "summary": summary,
        "cases": cases,
    }


def main() -> None:
    raw = GOLDEN_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("Cần ít nhất 15 câu hỏi thật từ corpus tuyển sinh")
    golden = json.loads(raw)
    if not isinstance(golden, list) or len(golden) < 15:
        raise ValueError("Cần ít nhất 15 câu hỏi thật từ corpus tuyển sinh")
    output = run_evaluation(golden)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(output['cases'])} measured cases to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

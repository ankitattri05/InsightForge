
"""
InsightForge A0 evaluation runner.

Runs all questions in eval/questions.yaml across supported domains.
Saves per-question responses, latency, execution status, causal-lint
output, and a consolidated run summary.

No unsupported accuracy scores are generated.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

from agent import narrator, tools
from engine.causal_linter import lint_causal_language


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_FILE = ROOT / "eval" / "questions.yaml"
RUNS_DIR = ROOT / "eval" / "runs"

DOMAIN_CONFIGS = {
    "telecom": ROOT / "config" / "telecom.yaml",
    "retail": ROOT / "config" / "retail.yaml",
}

EXPECTED_METRICS = {}


def load_questions() -> list[dict]:
    with QUESTIONS_FILE.open("r", encoding="utf-8") as file:
        content = yaml.safe_load(file)

    questions = content.get("questions", [])

    if not questions:
        raise ValueError("No evaluation questions found.")

    return questions


def save_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def run_question(question: dict, domain: str) -> dict:
    start = time.perf_counter()

    result = {
        "question_id": question["id"],
        "domain": domain,
        "question": question["question"],
        "test_type": question.get("test"),
        "answerable": question.get("answerable"),
        "status": "failed",
        "response": None,
        "latency_seconds": None,
        "causal_lint": None,
        "error": None,
    }

    try:
        response = narrator.answer(question["question"])
        latency = time.perf_counter() - start

        result["response"] = response
        result["latency_seconds"] = round(latency, 3)
        result["causal_lint"] = lint_causal_language(response)
        result["status"] = "completed"

    except Exception as exc:
        result["latency_seconds"] = round(
            time.perf_counter() - start, 3
        )
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def main() -> None:
    load_dotenv(ROOT / ".env")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model_name = os.getenv("ANTHROPIC_MODEL")

    if not api_key or not model_name:
        raise RuntimeError(
            "ANTHROPIC_API_KEY and ANTHROPIC_MODEL "
            "must be set in .env."
        )

    questions = load_questions()

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S_%fZ"
    )
    run_dir = RUNS_DIR / f"full_run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)

    narrator.initialize(
        api_key=api_key,
        model_name=model_name,
    )

    results = []
    initialized_domains = set()

    print(f"Starting evaluation: {len(questions)} questions")
    print(f"Results directory: {run_dir}")

    for question in questions:
        question_id = question["id"]
        domain = question["domain"].lower()

        print(f"\n[{question_id}] {domain}: {question['question']}")

        if domain not in DOMAIN_CONFIGS:
            result = {
                "question_id": question_id,
                "domain": domain,
                "question": question["question"],
                "test_type": question.get("test"),
                "answerable": question.get("answerable"),
                "status": "failed",
                "response": None,
                "latency_seconds": 0,
                "causal_lint": None,
                "error": f"Unsupported domain: {domain}",
            }
        else:
            if domain not in initialized_domains:
                try:
                    tools.initialize(
                        str(DOMAIN_CONFIGS[domain]),
                        EXPECTED_METRICS,
                    )
                    initialized_domains.add(domain)
                    print(f"Initialized {domain} configuration.")
                except Exception as exc:
                    result = {
                        "question_id": question_id,
                        "domain": domain,
                        "question": question["question"],
                        "test_type": question.get("test"),
                        "answerable": question.get("answerable"),
                        "status": "failed",
                        "response": None,
                        "latency_seconds": 0,
                        "causal_lint": None,
                        "error": (
                            f"Domain initialization failed: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                    }
                    results.append(result)
                    save_json(
                        run_dir / f"{question_id}.json",
                        result,
                    )
                    print(f"FAILED: {result['error']}")
                    continue

            result = run_question(question, domain)

        results.append(result)
        save_json(run_dir / f"{question_id}.json", result)

        if result["status"] == "completed":
            print(
                f"Completed in {result['latency_seconds']}s"
            )
        else:
            print(f"FAILED: {result['error']}")

    completed = [
        item for item in results
        if item["status"] == "completed"
    ]
    failed = [
        item for item in results
        if item["status"] == "failed"
    ]
    latencies = [
        item["latency_seconds"]
        for item in completed
        if item["latency_seconds"] is not None
    ]

    summary = {
        "benchmark_version": "1.0",
        "evaluation_type": "automated_multi_question",
        "started_at_utc": timestamp,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "completed": len(completed),
        "failed": len(failed),
        "completion_rate_pct": round(
            len(completed) / len(questions) * 100, 2
        ),
        "average_latency_seconds": (
            round(sum(latencies) / len(latencies), 3)
            if latencies else None
        ),
        "total_response_latency_seconds": round(
            sum(latencies), 3
        ),
        "domains": {
            domain: {
                "total": sum(
                    1 for item in results
                    if item["domain"] == domain
                ),
                "completed": sum(
                    1 for item in results
                    if item["domain"] == domain
                    and item["status"] == "completed"
                ),
                "failed": sum(
                    1 for item in results
                    if item["domain"] == domain
                    and item["status"] == "failed"
                ),
            }
            for domain in sorted(
                {item["domain"] for item in results}
            )
        },
        "results": results,
        "scoring_note": (
            "Numerical fidelity, entity binding, comparison direction, "
            "and causal-boundary correctness are not scored because "
            "validated per-question ground-truth answer keys and "
            "scoring rules are not yet available. Causal-lint output "
            "is recorded for review, not treated as a correctness score."
        ),
    }

    save_json(run_dir / "summary.json", summary)

    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total:     {len(questions)}")
    print(f"Completed: {len(completed)}")
    print(f"Failed:    {len(failed)}")
    print(f"Success:   {summary['completion_rate_pct']}%")
    print(
        f"Avg latency: "
        f"{summary['average_latency_seconds']} seconds"
    )
    print(f"\nSummary saved: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()

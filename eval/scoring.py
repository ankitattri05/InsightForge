import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORACLE_PATH = ROOT / "eval" / "oracle" / "ground_truth.json"
RUNS_PATH = ROOT / "eval" / "runs"


NUMBER_PATTERN = re.compile(
    r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_number(value):
    if value is None:
        return None

    text = str(value).strip()
    text = text.replace("₹", "").replace("$", "").replace(",", "")
    text = text.replace("pp", "").replace("PP", "")

    multiplier = 1.0
    lowered = text.lower()

    if lowered.endswith("cr"):
        multiplier = 10_000_000
        text = text[:-2]
    elif lowered.endswith("l"):
        multiplier = 100_000
        text = text[:-1]
    elif lowered.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif lowered.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]

    is_percent = text.endswith("%")
    text = text.strip().rstrip("%").strip()

    try:
        number = float(text) * multiplier
        return number / 100 if is_percent else number
    except ValueError:
        return None


def extract_numbers(text):
    values = []

    for match in NUMBER_PATTERN.findall(text or ""):
        value = normalize_number(match)
        if value is not None:
            values.append(value)

    return values


def approximately_equal(actual, expected):
    if expected == 0:
        return abs(actual) <= 0.01

    tolerance = max(abs(expected) * 0.005, 0.01)
    return abs(actual - expected) <= tolerance


def has_fallback(response):
    lowered = (response or "").lower()

    fallback_terms = [
        "i can't determine",
        "i cannot determine",
        "unable to determine",
        "not enough information",
        "insufficient information",
        "fallback",
    ]

    return any(term in lowered for term in fallback_terms)


def contains_expected_entity(response, expected_entity):
    return expected_entity.lower() in (response or "").lower()


def causal_boundary_passes(result):
    response = result.get("response", "")
    lint = result.get("causal_lint") or {}

    if not lint.get("passed", False):
        return False, "CAUSAL_VIOLATION"

    lowered = response.lower()

    boundary_terms = [
        "does not establish causation",
        "do not establish causation",
        "does not establish a causal relationship",
        "does not prove causation",
        "does not prove a causal relationship",
        "does not establish that",
        "do not establish that",
        "does not prove that",
        "does not confirm that",
        "does not explain why",
        "cannot conclude that",
        "cannot establish that",
        "cannot establish causality",
        "causation is not established",
        "causal relationship is not established",
        "not enough evidence to conclude",
        "not possible to determine",
        "rather than being explained by",
    ]

    if not any(term in lowered for term in boundary_terms):
        return False, "MISSING_BOUNDARY"

    return True, None


def score_numeric_question(result, oracle):
    response = result.get("response", "")

    if result.get("status") != "completed" or not response.strip():
        return "Safe fallback", "FALLBACK"

    if has_fallback(response):
        return "Safe fallback", "FALLBACK"

    expected = normalize_number(oracle["expected_value"])
    actual_values = extract_numbers(response)

    if expected is None or not actual_values:
        return "Wrong answer", "WRONG_NUMBER"

    if any(approximately_equal(value, expected) for value in actual_values):
        return "Correct", None

    return "Wrong answer", "WRONG_NUMBER"


def score_entity_question(result, oracle):
    response = result.get("response", "")

    if result.get("status") != "completed" or not response.strip():
        return "Safe fallback", "FALLBACK"

    if has_fallback(response):
        return "Safe fallback", "FALLBACK"

    expected_entity = oracle["expected_entity"]

    if not contains_expected_entity(response, expected_entity):
        return "Wrong answer", "WRONG_ENTITY"

    expected = normalize_number(oracle["expected_value"])
    actual_values = extract_numbers(response)

    if expected is not None and not any(
        approximately_equal(value, expected)
        for value in actual_values
    ):
        return "Wrong answer", "WRONG_NUMBER"

    return "Correct", None


def score_direction_question(result, oracle):
    response = result.get("response", "")
    expected_direction = oracle["direction"].lower()

    if result.get("status") != "completed" or not response.strip():
        return "Safe fallback", "FALLBACK"

    if has_fallback(response):
        return "Safe fallback", "FALLBACK"

    lowered = response.lower()

    direction_terms = {
        "increase": ["increase", "increased", "rising", "higher"],
        "decrease": ["decrease", "decreased", "falling", "lower"],
        "stable": ["stable", "unchanged", "flat"],
    }

    if not any(
        term in lowered
        for term in direction_terms.get(expected_direction, [])
    ):
        return "Wrong answer", "WRONG_DIRECTION"

    if expected_direction == "increase":
        opposite = ["decrease", "decreased", "falling", "lower"]
    elif expected_direction == "decrease":
        opposite = ["increase", "increased", "rising", "higher"]
    else:
        opposite = ["increase", "increased", "decrease", "decreased"]

    if any(term in lowered for term in opposite):
        return "Wrong answer", "WRONG_DIRECTION"

    return "Correct", None


def score_causal_question(result):
    passed, failure_code = causal_boundary_passes(result)

    if passed:
        return "Correct", None

    return "Wrong answer", failure_code


def score_question(result, oracle):
    question_id = result["question_id"]

    if oracle.get("test_type") == "causal_boundary":
        return score_causal_question(result)

    if question_id == "T09":
        response = result.get("response", "")

        if result.get("status") != "completed" or not response.strip():
            return "Safe fallback", "FALLBACK"

        if has_fallback(response):
            return "Safe fallback", "FALLBACK"

        lowered = response.lower()

        if "increase" not in lowered:
            return "Wrong answer", "WRONG_DIRECTION"

        if any(
            term in lowered
            for term in ["decrease", "decreased", "falling", "lower"]
        ):
            return "Wrong answer", "WRONG_DIRECTION"

        response_numbers = extract_numbers(response)

        expected_pp = float(oracle["percentage_point_change"])
        expected_relative = float(oracle["relative_change_pct"])

        if not any(
            approximately_equal(value, expected_pp)
            for value in response_numbers
        ):
            return "Wrong answer", "WRONG_NUMBER"

        percentage_values = [
            float(match.rstrip("%"))
            for match in re.findall(
                r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%",
                response,
            )
        ]

        if not any(
            approximately_equal(value, expected_relative)
            for value in percentage_values
        ):
            return "Wrong answer", "WRONG_NUMBER"

        return "Correct", None

    if question_id == "R07":
        response = result.get("response", "")

        if result.get("status") != "completed" or not response.strip():
            return "Safe fallback", "FALLBACK"

        if has_fallback(response):
            return "Safe fallback", "FALLBACK"

        expected_entity = oracle["expected_entity"]

        if not contains_expected_entity(response, expected_entity):
            return "Wrong answer", "WRONG_ENTITY"

        expected_profit = float(oracle["expected_value"])

        negative_numbers = [
            -float(match.replace(",", ""))
            for match in re.findall(
                r"-\s*[^0-9\s]*((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)",
                response,
            )
        ]

        if not any(
            approximately_equal(value, expected_profit)
            for value in negative_numbers
        ):
            return "Wrong answer", "WRONG_NUMBER"

        return "Correct", None

    if "expected_entity" in oracle:
        return score_entity_question(result, oracle)

    return score_numeric_question(result, oracle)


def find_latest_run():
    run_dirs = [
        path
        for path in RUNS_PATH.iterdir()
        if path.is_dir()
    ]

    if not run_dirs:
        raise FileNotFoundError("No evaluation runs found.")

    return max(run_dirs, key=lambda path: path.stat().st_mtime)


def load_run_results(run_dir):
    results = []

    for path in sorted(run_dir.glob("T*.json")):
        results.append(load_json(path))

    for path in sorted(run_dir.glob("R*.json")):
        results.append(load_json(path))

    if len(results) != 20:
        raise ValueError(
            f"Expected 20 question result files, found {len(results)}"
        )

    return results


def main():
    oracle = load_json(ORACLE_PATH)
    run_dir = find_latest_run()
    results = load_run_results(run_dir)

    scored_results = []
    correct = 0
    safe_fallback = 0
    wrong = 0

    for result in results:
        question_id = result["question_id"]
        oracle_result = oracle["questions"][question_id]

        classification, failure_code = score_question(
            result,
            oracle_result,
        )

        scored = {
            "question_id": question_id,
            "classification": classification,
            "failure_code": failure_code,
        }

        scored_results.append(scored)

        if classification == "Correct":
            correct += 1
        elif classification == "Safe fallback":
            safe_fallback += 1
        else:
            wrong += 1

    total = len(scored_results)

    report = {
        "oracle_version": oracle["version"],
        "run_directory": str(run_dir),
        "total_questions": total,
        "correct": correct,
        "safe_fallback": safe_fallback,
        "wrong": wrong,
        "fully_correct_rate": (
            correct / total if total else 0
        ),
        "results": scored_results,
    }

    output_path = run_dir / "score.json"

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Scored run: {run_dir.name}")
    print(f"Correct: {correct}/{total}")
    print(f"Safe fallback: {safe_fallback}/{total}")
    print(f"Wrong: {wrong}/{total}")
    print(f"Fully correct rate: {report['fully_correct_rate']:.2%}")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
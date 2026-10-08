import pytest

from eval.scoring import (
    normalize_number,
    score_question,
)


def test_percentage_normalization():
    assert normalize_number("9.99%") == pytest.approx(0.0999)
    assert normalize_number("11.96%") == pytest.approx(0.1196)


def test_currency_normalization():
    assert normalize_number("₹64,083.55") == 64083.55
    assert normalize_number("-64083.55") == -64083.55
    assert normalize_number("$64,083.55") == 64083.55


def test_numeric_question_correct():
    result = {
        "question_id": "T02",
        "status": "completed",
        "response": "Average resolution time is 248.84 minutes.",
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_value": "248.8422",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Correct"
    assert failure is None


def test_numeric_question_wrong_number():
    result = {
        "question_id": "T02",
        "status": "completed",
        "response": "Average resolution time is 300 minutes.",
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_value": "248.8422",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Wrong answer"
    assert failure == "WRONG_NUMBER"


def test_entity_question_wrong_entity():
    result = {
        "question_id": "T06",
        "status": "completed",
        "response": "Haryana has the highest SLA breach rate at 13.33%.",
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_entity": "Goa",
        "expected_value": "0.1333",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Wrong answer"
    assert failure == "WRONG_ENTITY"


def test_t09_wrong_direction():
    result = {
        "question_id": "T09",
        "status": "completed",
        "response": (
            "The latest 7-day comparison shows a Decrease "
            "of 2.6 percentage points and 27.78% relative change."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "percentage_point_change": "2.6000",
        "relative_change_pct": "27.77777778",
        "direction": "Increase",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Wrong answer"
    assert failure == "WRONG_DIRECTION"


def test_causal_boundary_violation():
    result = {
        "question_id": "T10",
        "status": "completed",
        "response": (
            "The vendor caused the higher SLA breach rate."
        ),
        "causal_lint": {
            "passed": False,
            "violations": ["causal_claim"],
        },
    }

    oracle = {
        "test_type": "causal_boundary",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Wrong answer"
    assert failure == "CAUSAL_VIOLATION"


def test_safe_fallback():
    result = {
        "question_id": "T02",
        "status": "completed",
        "response": "I cannot determine the answer from the available data.",
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_value": "248.8422",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Safe fallback"
    assert failure == "FALLBACK"


def test_r07_negative_profit():
    result = {
        "question_id": "R07",
        "status": "completed",
        "response": (
            "Tables is the lowest-profit subcategory with "
            "a profit of -₹64,083.55."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_entity": "Tables",
        "expected_value": "-64083.55",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Correct"
    assert failure is None


def test_r07_wrong_sign():
    result = {
        "question_id": "R07",
        "status": "completed",
        "response": (
            "Tables is the lowest-profit subcategory with "
            "a profit of ₹64,083.55."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "expected_entity": "Tables",
        "expected_value": "-64083.55",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Wrong answer"
    assert failure == "WRONG_NUMBER"

def test_r09_causal_boundary_with_do_not_establish():
    result = {
        "question_id": "R09",
        "status": "completed",
        "response": (
            "The verified findings do not establish causation between "
            "the highest-profit category and the total profit figure."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "test_type": "causal_boundary",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Correct"
    assert failure is None

def test_r09_causal_boundary_with_rather_than_explained_by():
    result = {
        "question_id": "R09",
        "status": "completed",
        "response": (
            "All three categories contributed positively to the total profit, "
            "meaning total profit reflects a combined contribution across the "
            "categories rather than being explained by any single one."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "test_type": "causal_boundary",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Correct"
    assert failure is None

def test_r09_causal_boundary_with_do_not_establish_that():
    result = {
        "question_id": "R09",
        "status": "completed",
        "response": (
            "The diagnostics identify observed contributor rankings only; "
            "they do not establish that Technology's contribution caused "
            "or explains the total profit outcome."
        ),
        "causal_lint": {"passed": True},
    }

    oracle = {
        "test_type": "causal_boundary",
    }

    classification, failure = score_question(result, oracle)

    assert classification == "Correct"
    assert failure is None

def test_fault_injection_wrong_numeric():
    result = {'question_id': 'T02', 'status': 'completed', 'response': 'Average resolution time is 300 minutes.', 'causal_lint': {'passed': True}}
    oracle = {'expected_value': '248.8422'}
    classification, failure = score_question(result, oracle)
    assert classification == 'Wrong answer'
    assert failure == 'WRONG_NUMBER'

def test_fault_injection_wrong_entity():
    result = {'question_id': 'T06', 'status': 'completed', 'response': 'Haryana has the highest SLA breach rate at 13.33%.', 'causal_lint': {'passed': True}}
    oracle = {'expected_entity': 'Goa', 'expected_value': '0.1333'}
    classification, failure = score_question(result, oracle)
    assert classification == 'Wrong answer'
    assert failure == 'WRONG_ENTITY'

def test_fault_injection_wrong_direction():
    result = {'question_id': 'T09', 'status': 'completed', 'response': 'The latest comparison shows a Decrease of 2.6 percentage points and 27.78% relative change.', 'causal_lint': {'passed': True}}
    oracle = {'percentage_point_change': '2.6000', 'relative_change_pct': '27.77777778', 'direction': 'Increase'}
    classification, failure = score_question(result, oracle)
    assert classification == 'Wrong answer'
    assert failure == 'WRONG_DIRECTION'

def test_fault_injection_causal_claim():
    result = {'question_id': 'T10', 'status': 'completed', 'response': 'The vendor caused the higher SLA breach rate.', 'causal_lint': {'passed': False, 'violations': ['causal_claim']}}
    oracle = {'test_type': 'causal_boundary'}
    classification, failure = score_question(result, oracle)
    assert classification == 'Wrong answer'
    assert failure == 'CAUSAL_VIOLATION'

def test_fault_injection_currency_corruption():
    result = {'question_id': 'R01', 'status': 'completed', 'response': 'Total sales were ,000,000.00.', 'causal_lint': {'passed': True}}
    oracle = {'expected_value': '12642905.00'}
    classification, failure = score_question(result, oracle)
    assert classification == 'Wrong answer'
    assert failure == 'WRONG_NUMBER'



from engine.causal_linter import (
    find_causal_language,
    lint_causal_language,
)


def test_clean_text_passes():
    text = "Incidents increased by 12% while SLA breaches remained stable."

    result = lint_causal_language(text)

    assert result["passed"] is True
    assert result["violations"] == []
    assert result["violation_count"] == 0


def test_because_is_flagged():
    text = "Incidents increased because resolution time increased."

    result = lint_causal_language(text)

    assert result["passed"] is False
    assert "because" in result["violations"]


def test_multiple_causal_phrases_are_flagged():
    text = (
        "Higher dispatch costs caused total cost to rise, "
        "which led to higher cost per incident."
    )

    result = lint_causal_language(text)

    assert result["passed"] is False
    assert "caused" in result["violations"]
    assert "led to" in result["violations"]
    assert result["violation_count"] == 2


def test_case_insensitive_matching():
    text = "The increase was CAUSED by higher dispatch volume."

    found = find_causal_language(text)

    assert "CAUSED" in found
def test_explicit_causal_denial_passes():
    text = 'The ranking does not establish that Optical Network caused the overall SLA problem.'
    result = lint_causal_language(text)
    assert result['passed'] is True
    assert result['violations'] == []

def test_causation_denial_passes():
    text = 'The highest-ranked contributor does not prove causation.'
    result = lint_causal_language(text)
    assert result['passed'] is True
    assert result['violations'] == []

def test_causal_language_inside_denial_passes():
    text = (
        "The deterministic diagnostic interpretation explicitly states "
        "that this association does not establish root cause or causality. "
        "The rankings do not explain why the overall rate reached its "
        "current level or confirm that any single contributor caused it."
    )

    result = lint_causal_language(text)

    assert result["passed"] is True
    assert result["violations"] == []
    assert result["violation_count"] == 0

def test_not_what_caused_denial_passes():
    text = (
        "These rankings identify where investigation should begin, "
        "not what caused the overall SLA breach rate."
    )

    result = lint_causal_language(text)

    assert result["passed"] is True
    assert result["violations"] == []
    assert result["violation_count"] == 0
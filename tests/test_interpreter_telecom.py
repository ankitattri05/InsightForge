import pytest

from engine.interpreter_telecom import _interpret_sla_comparison


@pytest.mark.parametrize(
    ("classification", "expected_phrase"),
    [
        (
            "material_signal",
            "statistically established",
        ),
        (
            "not_statistically_established",
            "does not statistically establish a change",
        ),
        (
            "below_materiality_threshold",
            "below the configured materiality threshold",
        ),
        (
            "unknown_classification",
            "no supported interpretation is defined",
        ),
    ],
)
def test_sla_comparison_interpretation_mapping(
    classification,
    expected_phrase,
):
    result = _interpret_sla_comparison(
        {
            "materiality": {
                "classification": classification,
            }
        }
    )

    assert result["classification"] == classification
    assert expected_phrase in result["meaning"]


def test_sla_comparison_interpretation_when_comparison_unavailable():
    result = _interpret_sla_comparison(None)

    assert result["classification"] == "unavailable"
    assert "No comparable prior period is available" in result["meaning"]
    assert "A trend conclusion cannot be established" in result["meaning"]


def test_sla_comparison_interpretation_when_classification_missing():
    result = _interpret_sla_comparison(
        {
            "materiality": {},
        }
    )

    assert result["classification"] == "unclassified"
    assert "no supported interpretation is defined" in result["meaning"]

from engine import interpreter_telecom as interpreter


@pytest.mark.parametrize(
    "classification",
    [
        "material_signal",
        "not_statistically_established",
        "below_materiality_threshold",
    ],
)
def test_sla_status_is_independent_of_comparison_classification(
    monkeypatch,
    classification,
):
    monkeypatch.setattr(interpreter, "get_source", lambda *args: "vw_incident_flat")
    monkeypatch.setattr(
        interpreter,
        "compare_periods",
        lambda *args, **kwargs: {
            "materiality": {"classification": classification}
        },
    )
    monkeypatch.setattr(interpreter, "multi_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(interpreter, "_base_finding", lambda *args, **kwargs: {})

    config = {
        "thresholds": {
            "sla_breach_rate": {
                "good": 0.05,
                "warning": 0.10,
            }
        }
    }

    finding = interpreter.interpret_metric("sla_breach_rate", 0.15, config)

    assert finding["status"] == "Critical"
    assert finding["comparison_interpretation"]["classification"] == classification
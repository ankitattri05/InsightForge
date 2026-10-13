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


def test_sla_diagnostic_interpretation_defines_measurable_action():
    diagnostics = {
        "top_fault": [
            {
                "category": "Optical Network",
                "minimum_n_met": True,
                "display": "19.74%",
                "value": 0.1974,
                "overall_rate": 0.0999,
                "excess_vs_overall_pp": 9.75,
                "n": 6420,
                "observed_breaches": 1267,
                "benchmark_breaches": 641,
                "excess_breaches": 626,
                "incident_share": 0.257,
                "breach_share": 0.507,
                "cost": 1546035350.92,
                "cost_share": 0.498,
                "breach_concentration": 1.98,
                "cost_concentration": 1.94,
            }
        ],
        "top_vendor": [
            {
                "category": "Tejas",
                "minimum_n_met": True,
                "display": "14.92%",
                "n": 4116,
                "observed_breaches": 614,
            }
        ],
        "excess_breach_fault": [
            {"category": "Optical Network", "excess_breaches": 626}
        ],
        "excess_breach_vendor": [
            {"category": "Tejas", "excess_breaches": 203}
        ],
        "excess_breach_state": [
            {"category": "Punjab", "excess_breaches": 19}
        ],
    }

    result = interpreter._interpret_sla_diagnostics(diagnostics)
    meaning = result["meaning"].lower()

    assert result["status"] == "priority_for_investigation"
    assert "investigate" in meaning
    assert "pre-intervention breach-rate baseline" in meaning
    assert "comparable reporting windows" in meaning
    assert "incident volume" in meaning
    assert "resolution time" in meaning
    assert "cost" in meaning
    assert "target must be agreed before the" in meaning
    assert "not" in meaning
    assert "recoverable savings" in meaning
    assert "does not establish root cause or causality" in meaning


import pytest

from agent import narrator

from types import SimpleNamespace


@pytest.fixture
def telecom_diagnostics(monkeypatch):
    monkeypatch.setattr(
    narrator,
    "_client",
    SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="text",
                        text="MOCK_LLM_RESPONSE",
                    )
                ]
            )
        )
    ),
)
    monkeypatch.setattr(narrator, "_model", "test-model")
    monkeypatch.setattr(narrator, "_system_prompt", "test prompt")

    monkeypatch.setattr(
        narrator.tools,
        "get_config",
        lambda: {"project": {"name": "Telecom Service Assurance"}},
    )

    monkeypatch.setattr(
        narrator,
        "validate_finding_interpretations",
        lambda findings: {"passed": True, "errors": []},
    )

    monkeypatch.setattr(
        narrator,
        "reporting_period",
        lambda config: {
            "start_date": "2023-01-01",
            "end_date": "2025-12-31",
        },
    )


    finding = {
        "status": "Warning",
        "business_meaning": "SLA breaches affect service quality.",
        "interpretation": "The observed breach rate is above the expected level.",
        "diagnostics": {
            "top_vendor": [
                {
                    "category": "Tejas",
                    "display": "14.92%",
                    "n": 4116,
                    "observed_breaches": 614.11,
                    "minimum_n_met": True,
                }
            ],
            "top_fault": [
                {
                    "category": "Optical Network",
                    "display": "19.74%",
                    "n": 6417,
                    "observed_breaches": 1267,
                    "excess_breaches": 626,
                    "minimum_n_met": True,
                }
            ],
        },
    }



    monkeypatch.setattr(
        narrator.tools,
        "get_metric",
        lambda metric_name: {
            "success": True,
            "data": {
                "metric": metric_name,
                "display_value": "9.99%",
                "finding": finding,
            },
        },
    )



def test_vendor_ranking_uses_verified_diagnostics(telecom_diagnostics):
    answer = narrator.answer(
        "Which vendor has the highest SLA breach rate, "
        "and how many incidents support that ranking?"
    )

    assert "Tejas" in answer
    assert "14.92%" in answer
    assert "4,116 incidents" in answer
    assert "614 breaches" in answer



def test_fault_priority_uses_general_analysis_path(telecom_diagnostics):
    answer = narrator.answer(
        "Which fault category should operations prioritize, "
        "and what evidence supports the decision?"
    )

    assert answer == "MOCK_LLM_RESPONSE"

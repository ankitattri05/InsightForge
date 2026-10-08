
from agent import narrator


def test_generate_brief_includes_deterministic_comparison_interpretation(
    monkeypatch,
):
    captured = {}

    finding = {
        "finding_id": "F-SLA-BREACH-RATE",
        "status": "watch",
        "business_meaning": "SLA breach rate",
        "interpretation": "The SLA breach rate increased.",
        "headline": "SLA breach rate increased",
        "diagnostics": {},
        "evidence": [],
        "comparison": {
            "window": "Current vs previous period",
            "previous": 0.09,
            "current": 0.12,
            "direction": "increase",
            "change_pct": 3.0,
        },
        "comparison_interpretation": {
            "classification": "not_statistically_established",
            "meaning": (
                "The change meets the configured materiality threshold, "
                "but the evidence does not establish a statistically "
                "significant change."
            ),
        },
    }

    results = [
        {
            "success": True,
            "data": {
                "finding": finding,
                "metric": "sla_breach_rate",
                "display_value": "12%",
            },
        }
    ]

    class FakeMessages:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]

            class Response:
                content = [
                    type(
                        "TextBlock",
                        (),
                        {"type": "text", "text": "Test brief"},
                    )()
                ]

            return Response()

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(narrator, "_client", FakeClient())
    monkeypatch.setattr(narrator, "_model", "test-model")
    monkeypatch.setattr(narrator, "_system_prompt", "Test system prompt")

    monkeypatch.setattr(narrator.tools, "get_metrics", lambda names: results)
    monkeypatch.setattr(
        narrator.tools,
        "get_config",
        lambda: {
            "database": {"view": "vw_incident_flat"},
            "dataset": {"date_column": "Open_Time"},
            "project": {"name": "Telecom Service Assurance", "version": "1.0"},
        },
    )
    monkeypatch.setattr(
        narrator,
        "generate_scorecard",
        lambda results, config: "Test scorecard",
    )
    monkeypatch.setattr(
        narrator,
        "reporting_period",
        lambda **kwargs: {
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
        },
    )

    narrator.generate_brief(["sla_breach_rate"])

    prompt = captured["prompt"]

    assert "Deterministic Comparison Interpretation:" in prompt
    assert "not_statistically_established" in prompt
    assert "does not establish a statistically significant change" in prompt

def test_answer_includes_deterministic_comparison_interpretation(
    monkeypatch,
):
    captured = {}

    finding = {
        "finding_id": "F-SLA-BREACH-RATE",
        "status": "watch",
        "business_meaning": "SLA breach rate",
        "interpretation": "The SLA breach rate increased.",
        "headline": "SLA breach rate increased",
        "diagnostics": {},
        "evidence": [],
        "comparison_interpretation": {
            "classification": "not_statistically_established",
            "meaning": (
                "The change meets the configured materiality threshold, "
                "but the evidence does not establish a statistically "
                "significant change."
            ),
        },
    }

    results = [
        {
            "success": True,
            "data": {
                "finding": finding,
                "metric": "sla_breach_rate",
                "display_value": "12%",
            },
        }
    ]

    class FakeMessages:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]

            class Response:
                content = [
                    type(
                        "TextBlock",
                        (),
                        {"type": "text", "text": "Test answer"},
                    )()
                ]

            return Response()

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(narrator, "_client", FakeClient())
    monkeypatch.setattr(narrator, "_model", "test-model")
    monkeypatch.setattr(narrator, "_system_prompt", "Test system prompt")

    monkeypatch.setattr(
        narrator.tools,
        "get_config",
        lambda: {
            "project": {"name": "Telecom Service Assurance"},
            "database": {"view": "vw_incident_flat"},
            "dataset": {"date_column": "Open_Time"},
        },
    )
    monkeypatch.setattr(
        narrator.tools,
        "get_metrics",
        lambda names: results,
    )
    monkeypatch.setattr(
        narrator,
        "reporting_period",
        lambda **kwargs: {
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
        },
    )

    narrator.answer("What is the SLA breach rate?")

    prompt = captured["prompt"]

    assert "Deterministic Comparison Interpretation:" in prompt
    assert "not_statistically_established" in prompt
    assert "does not establish a statistically significant change" in prompt

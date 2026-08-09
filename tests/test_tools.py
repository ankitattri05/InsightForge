from tests.test_metrics import sqlite_engine
import pytest

from agent import tools


EXPECTED = {
    "incident_count": 3,
    "sla_breach_rate": 2 / 3,
    "avg_resolution_time": 240.0,
    "total_cost": 6000.0,
}


def test_tool_requires_initialization():
    tools._validation_passed = False

    with pytest.raises(RuntimeError):
        tools.get_metric("incident_count")


def test_initialize(sqlite_engine):
    tools.initialize(
        "config/telecom.yaml",
        EXPECTED,
    )

    assert tools._validation_passed is True


def test_get_metric(sqlite_engine):
    result = tools.get_metric("incident_count")

    assert result["success"] is True
    assert result["data"]["metric"] == "incident_count"
    assert result["data"]["value"] == 3


def test_unknown_metric(sqlite_engine):
    result = tools.get_metric("unknown_metric")

    assert result["success"] is False
    assert result["error"] == "Unknown KPI: 'unknown_metric'"


def test_get_metrics(sqlite_engine):
    results = tools.get_metrics(
        [
            "incident_count",
            "total_cost",
        ]
    )

    assert len(results) == 2

    assert all(
        result["success"]
        for result in results
    )
import pytest
from sqlalchemy import text

from agent import tools
from tests.test_metrics import sqlite_engine as metrics_sqlite_engine


EXPECTED = {
    "incident_count": 3,
    "sla_breach_rate": 2 / 3,
    "avg_resolution_time": 240.0,
    "total_cost": 6000.0,
}


@pytest.fixture
def sqlite_engine(metrics_sqlite_engine):
    """
    Extend the shared metrics fixture with the columns required by
    the telecom semantic audit.
    """

    dimensions = [
        "State_UT",
        "City",
        "Zone",
        "Vendor",
        "Technology",
        "Severity",
        "Fault_Category",
        "Resolution_Type",
    ]

    measures = [
        "Customers_Impacted",
        "Dispatch_Cost",
    ]

    flags = [
        "Repeat_Fault_Flag",
        "Escalation_Flag",
    ]

    with metrics_sqlite_engine.begin() as connection:
        for column in dimensions:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE vw_incident_flat
                    ADD COLUMN {column} TEXT
                    """
                )
            )

        for column in measures:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE vw_incident_flat
                    ADD COLUMN {column} REAL
                    """
                )
            )

        for column in flags:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE vw_incident_flat
                    ADD COLUMN {column} INTEGER
                    """
                )
            )

        connection.execute(
            text(
                """
                UPDATE vw_incident_flat
                SET
                    State_UT = 'Test State',
                    City = 'Test City',
                    Zone = 'Test Zone',
                    Vendor = 'Test Vendor',
                    Technology = 'GPON',
                    Severity = 'Medium',
                    Fault_Category = 'Test Fault',
                    Resolution_Type = 'Standard',
                    Customers_Impacted = 100,
                    Dispatch_Cost = 50,
                    Repeat_Fault_Flag = 0,
                    Escalation_Flag = 0
                """
            )
        )

    return metrics_sqlite_engine


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

    finding = result["data"]["finding"]

    assert finding["finding_id"] == "F-INCIDENT_COUNT"

    # G1 Evidence Contract
    assert finding["n"] == 3
    assert finding["unit"] == "incidents"
    assert finding["definition"]
    assert finding["additive"] is True
    assert finding["additive_across"]
    assert "State_UT" in finding["additive_across"]
    assert finding["evidence_class"] == "descriptive"
    assert isinstance(finding["not_established"], list)

    evidence = finding["evidence"]

    assert evidence
    assert evidence[0]["source_query_id"] == "kpi:incident_count"
    assert evidence[0]["source_view"] == "vw_incident_flat"
    assert "SELECT" in evidence[0]["sql"]


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
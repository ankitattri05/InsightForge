"""
Ground-truth validation tests.

These tests verify that the validation layer correctly compares
analytics results with approved business values.
"""

import pytest
from sqlalchemy import text

from engine.config_loader import load_config
from engine.db import get_engine, reset_engine
from engine.validation import validate_metric, validate_metrics


@pytest.fixture
def config():
    return load_config("config/telecom.yaml")


@pytest.fixture
def sqlite_engine():
    reset_engine()

    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    engine = get_engine()

    with engine.begin() as conn:

        conn.execute(text("""
            CREATE TABLE vw_incident_flat (
                Incident_ID INTEGER,
                Resolution_Minutes REAL,
                Estimated_Total_Incident_Cost REAL,
                SLA_Breach_Flag INTEGER
            )
        """))

        conn.execute(text("""
            INSERT INTO vw_incident_flat
            VALUES
            (1,120,1000,0),
            (2,240,2000,1),
            (3,360,3000,1)
        """))

    return engine


EXPECTED = {
    "incident_count": 3,
    "sla_breach_rate": 2 / 3,
    "avg_resolution_time": 240.0,
    "total_cost": 6000.0,
}


def test_validate_single_metric(config, sqlite_engine):
    result = validate_metric(
        "incident_count",
        3,
        config,
    )

    assert result["passed"] is True


def test_validate_all_metrics(config, sqlite_engine):
    results = validate_metrics(EXPECTED, config)

    failures = [r for r in results if not r["passed"]]

    assert failures == []
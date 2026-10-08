import os

import pytest
from sqlalchemy import text

from engine.config_loader import load_config
from engine.metrics import calculate_metric


@pytest.fixture
def config():
    return load_config("config/telecom.yaml")


@pytest.fixture
def sqlite_engine():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from engine.db import get_engine, reset_engine

    reset_engine()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE vw_incident_flat (
                    Date TEXT,
                    Incident_ID INTEGER,
                    Resolution_Minutes REAL,
                    Estimated_Total_Incident_Cost REAL,
                    SLA_Breach_Flag INTEGER
                )
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO vw_incident_flat
                VALUES
                    ('2026-01-03', 1, 120, 1000, 0),
                    ('2026-01-02', 2, 240, 2000, 1),
                    ('2025-12-28', 3, 360, 3000, 1)
                """
            )
        )

    return engine


def test_incident_count(config, sqlite_engine):
    assert calculate_metric(
        "incident_count",
        config,
    ) == 3.0


def test_total_cost(config, sqlite_engine):
    assert calculate_metric(
        "total_cost",
        config,
    ) == 6000.0


def test_sla_breach_rate(config, sqlite_engine):
    assert calculate_metric(
        "sla_breach_rate",
        config,
    ) == pytest.approx(2 / 3)


def test_avg_resolution_time(config, sqlite_engine):
    assert calculate_metric(
        "avg_resolution_time",
        config,
    ) == 240.0
from datetime import date

from sqlalchemy import create_engine, text

from engine.period_metrics import period_kpi_value


def _setup_database():

    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                CREATE TABLE incidents (
                    Incident_ID INTEGER,
                    Date DATE,
                    Estimated_Total_Incident_Cost REAL
                )
                """
            )
        )

        connection.execute(
            text(
                """
                INSERT INTO incidents
                (Incident_ID, Date, Estimated_Total_Incident_Cost)
                VALUES
                (1, '2026-01-01', 100),
                (2, '2026-01-02', 200),
                (3, '2026-01-03', 300),
                (4, '2026-01-10', 400)
                """
            )
        )

    return engine


def test_period_incident_count(monkeypatch):

    engine = _setup_database()

    monkeypatch.setattr(
        "engine.period_metrics.get_engine",
        lambda: engine,
    )

    config = {
        "dataset": {
            "date_column": "Date",
        },
        "kpis": {
            "incident_count": {
                "type": "count",
            },
        },
    }

    result = period_kpi_value(
        metric_name="incident_count",
        source="incidents",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        config=config,
    )

    assert result == 3.0


def test_period_total_cost(monkeypatch):

    engine = _setup_database()

    monkeypatch.setattr(
        "engine.period_metrics.get_engine",
        lambda: engine,
    )

    config = {
        "dataset": {
            "date_column": "Date",
        },
        "kpis": {
            "total_cost": {
                "type": "sum",
                "column": "Estimated_Total_Incident_Cost",
            },
        },
    }

    result = period_kpi_value(
        metric_name="total_cost",
        source="incidents",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        config=config,
    )

    assert result == 600.0


def test_period_cost_per_incident(monkeypatch):

    engine = _setup_database()

    monkeypatch.setattr(
        "engine.period_metrics.get_engine",
        lambda: engine,
    )

    config = {
        "dataset": {
            "date_column": "Date",
        },
        "kpis": {
            "incident_count": {
                "type": "count",
            },
            "total_cost": {
                "type": "sum",
                "column": "Estimated_Total_Incident_Cost",
            },
            "cost_per_incident": {
                "type": "calculated",
            },
        },
    }

    result = period_kpi_value(
        metric_name="cost_per_incident",
        source="incidents",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        config=config,
    )

    assert result == 200.0

def test_cost_bridge_periods(monkeypatch):

    engine = _setup_database()

    monkeypatch.setattr(
        "engine.period_metrics.get_engine",
        lambda: engine,
    )

    config = {
        "dataset": {
            "date_column": "Date",
        },
        "kpis": {
            "incident_count": {
                "type": "count",
            },
            "total_cost": {
                "type": "sum",
                "column": "Estimated_Total_Incident_Cost",
            },
            "cost_per_incident": {
                "type": "calculated",
            },
        },
    }

    from engine.period_metrics import cost_bridge_periods

    result = cost_bridge_periods(
        source="incidents",
        previous_start=date(2026, 1, 1),
        previous_end=date(2026, 1, 2),
        current_start=date(2026, 1, 3),
        current_end=date(2026, 1, 3),
        config=config,
    )

    assert result is not None
    assert result["previous_volume"] == 2.0
    assert result["current_volume"] == 1.0
    assert result["previous_rate"] == 150.0
    assert result["current_rate"] == 300.0
    assert result["previous_value"] == 300.0
    assert result["current_value"] == 300.0
    assert result["absolute_change"] == 0.0
    assert result["reconciles"] is True
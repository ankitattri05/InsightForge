from datetime import date

import pytest
from sqlalchemy import create_engine, text

from engine.comparison import compare_periods


def _create_engine_with_data(rows):
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE vw_incident_flat (
                    Date DATE,
                    Incident_ID INTEGER,
                    SLA_Breach_Flag REAL
                )
                """
            )
        )

        if rows:
            connection.execute(
                text(
                    """
                    INSERT INTO vw_incident_flat
                        (Date, Incident_ID, SLA_Breach_Flag)
                    VALUES
                        (:date, :incident_id, :breach)
                    """
                ),
                rows,
            )

    return engine


def _make_rate_rows(
    previous_breaches,
    current_breaches,
    n=100,
):
    rows = []

    for day, breaches in [
        (date(2025, 1, 1), previous_breaches),
        (date(2025, 1, 2), current_breaches),
    ]:
        for i in range(n):
            rows.append(
                {
                    "date": day,
                    "incident_id": len(rows) + 1,
                    "breach": 1 if i < breaches else 0,
                }
            )

    return rows


def _compare_rate(rows):
    engine = _create_engine_with_data(rows)

    return compare_periods(
        aggregation="AVG",
        column="SLA_Breach_Flag",
        view="vw_incident_flat",
        window_days=1,
        engine=engine,
        metric_type="rate",
        config={
            "materiality": {
                "minimum_n": 30,
                "minimum_rate_change_pp": 1.0,
                "significance_level": 0.05,
            }
        },
    )


def test_compare_periods():
    engine = _create_engine_with_data(
        [
            {
                "date": date(2025, 1, 1),
                "incident_id": 1,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 2),
                "incident_id": 2,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 3),
                "incident_id": 3,
                "breach": 1,
            },
            {
                "date": date(2025, 1, 4),
                "incident_id": 4,
                "breach": 1,
            },
        ]
    )

    result = compare_periods(
        aggregation="COUNT",
        column="*",
        view="vw_incident_flat",
        window_days=2,
        engine=engine,
    )

    assert result is not None
    assert result["current"] == 2.0
    assert result["previous"] == 2.0
    assert result["change_pct"] == 0.0
    assert result["relative_change_pct"] == 0.0
    assert result["absolute_delta"] == 0.0
    assert result["current_n"] == 2
    assert result["previous_n"] == 2


def test_rate_comparison_returns_percentage_points():
    engine = _create_engine_with_data(
        [
            {
                "date": date(2025, 1, 1),
                "incident_id": 1,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 2),
                "incident_id": 2,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 3),
                "incident_id": 3,
                "breach": 1,
            },
            {
                "date": date(2025, 1, 4),
                "incident_id": 4,
                "breach": 1,
            },
        ]
    )

    result = compare_periods(
        aggregation="AVG",
        column="SLA_Breach_Flag",
        view="vw_incident_flat",
        window_days=2,
        engine=engine,
        metric_type="rate",
    )

    assert result is not None
    assert result["previous"] == 0.0
    assert result["current"] == 1.0
    assert result["absolute_delta"] == 1.0
    assert result["percentage_point_change"] == 100.0
    assert result["relative_change_pct"] is None
    assert result["change_pct"] is None

    assert result["previous_numerator"] == 0.0
    assert result["previous_denominator"] == 2
    assert result["current_numerator"] == 2.0
    assert result["current_denominator"] == 2


def test_previous_zero_is_safe():
    engine = _create_engine_with_data(
        [
            {
                "date": date(2025, 1, 1),
                "incident_id": 1,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 2),
                "incident_id": 2,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 3),
                "incident_id": 3,
                "breach": 0,
            },
            {
                "date": date(2025, 1, 4),
                "incident_id": 4,
                "breach": 1,
            },
        ]
    )

    result = compare_periods(
        aggregation="AVG",
        column="SLA_Breach_Flag",
        view="vw_incident_flat",
        window_days=2,
        engine=engine,
        metric_type="rate",
    )

    assert result is not None
    assert result["previous"] == 0.0
    assert result["current"] == 0.5
    assert result["relative_change_pct"] is None
    assert result["change_pct"] is None
    assert result["percentage_point_change"] == 50.0

    assert result["previous_numerator"] == 0.0
    assert result["previous_denominator"] == 2
    assert result["current_numerator"] == 1.0
    assert result["current_denominator"] == 2


def test_material_signal_classification():
    result = _compare_rate(
        _make_rate_rows(
            previous_breaches=10,
            current_breaches=30,
        )
    )

    assert result is not None
    materiality = result["materiality"]

    assert materiality["classification"] == "material_signal"
    assert materiality["material"] is True
    assert materiality["p_value"] < 0.05


def test_not_statistically_established_classification():
    result = _compare_rate(
        _make_rate_rows(
            previous_breaches=10,
            current_breaches=12,
        )
    )

    assert result is not None
    materiality = result["materiality"]

    assert (
        materiality["classification"]
        == "not_statistically_established"
    )
    assert materiality["material"] is True
    assert materiality["p_value"] >= 0.05


def test_below_materiality_threshold_classification():
    result = _compare_rate(
        _make_rate_rows(
            previous_breaches=20,
            current_breaches=21,
            n=200,
        )
    )

    assert result is not None
    materiality = result["materiality"]

    assert (
        materiality["classification"]
        == "below_materiality_threshold"
    )
    assert materiality["change_meets_threshold"] is False
    assert materiality["material"] is False


def test_invalid_window_is_rejected():
    engine = _create_engine_with_data([])

    with pytest.raises(ValueError):
        compare_periods(
            aggregation="COUNT",
            column="*",
            view="vw_incident_flat",
            window_days=0,
            engine=engine,
        )
"""
InsightForge Historical Comparison Engine

Provides deterministic period-over-period comparison.

Principles
----------
- Uses dataset dates, never system time.
- Current period is anchored to MAX(Date).
- Returns None when insufficient history exists.
- Performs arithmetic only.
- Distinguishes relative change from percentage-point change.
- Preserves the existing change_pct contract for compatibility.
- Materiality thresholds come from configuration.
- Statistical evidence is experimental and limited to rate KPIs.
- Never generates business narratives.
"""

from datetime import date, timedelta
from math import erfc, sqrt

from sqlalchemy import text

from engine.db import get_engine


def _latest_date(view: str, engine=None) -> date:
    """
    Return the latest date present in the dataset.

    "Current" is always anchored to the data itself,
    never to the system clock.
    """

    sql = text(
        f"""
        SELECT MAX(Date)
        FROM {view}
        """
    )

    db_engine = engine or get_engine()

    with db_engine.connect() as connection:
        latest = connection.execute(sql).scalar()

    if isinstance(latest, date):
        return latest

    if isinstance(latest, str):
        return date.fromisoformat(latest)

    if isinstance(latest, int):
        return date.fromisoformat(str(latest))

    return latest


def _aggregate_period(
    aggregation: str,
    column: str,
    view: str,
    start_date,
    end_date,
    engine=None,
) -> float | None:
    """
    Aggregate one metric over a date range.
    """

    sql = text(
        f"""
        SELECT {aggregation}({column})
        FROM {view}
        WHERE Date BETWEEN :start_date AND :end_date
        """
    )

    db_engine = engine or get_engine()

    with db_engine.connect() as connection:
        result = connection.execute(
            sql,
            {
                "start_date": start_date,
                "end_date": end_date,
            },
        ).scalar()

    if result is None:
        return None

    return float(result)


def _count_period_rows(
    view: str,
    start_date,
    end_date,
    engine=None,
) -> int:
    """
    Return the number of source rows in a reporting window.
    """

    sql = text(
        f"""
        SELECT COUNT(*)
        FROM {view}
        WHERE Date BETWEEN :start_date AND :end_date
        """
    )

    db_engine = engine or get_engine()

    with db_engine.connect() as connection:
        result = connection.execute(
            sql,
            {
                "start_date": start_date,
                "end_date": end_date,
            },
        ).scalar()

    return int(result or 0)


def _two_proportion_p_value(
    current_successes: float,
    current_n: int,
    previous_successes: float,
    previous_n: int,
) -> float | None:
    """
    Calculate a two-sided pooled two-proportion z-test p-value.

    Experimental diagnostic only. Assumes independent binary
    observations and is not a multiple-testing correction.
    """

    if current_n <= 0 or previous_n <= 0:
        return None

    pooled_rate = (
        current_successes + previous_successes
    ) / (current_n + previous_n)

    standard_error = sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / current_n + 1 / previous_n)
    )

    if standard_error == 0:
        return None

    z_score = (
        current_successes / current_n
        - previous_successes / previous_n
    ) / standard_error

    return erfc(abs(z_score) / sqrt(2))


def compare_periods(
    aggregation: str,
    column: str,
    view: str,
    window_days: int = 7,
    engine=None,
    metric_type: str | None = None,
    config: dict | None = None,
) -> dict | None:
    """
    Compare the latest reporting window against the previous window.

    For rate KPIs:
        - absolute_delta is the raw difference
        - percentage_point_change is the difference expressed in pp
        - relative_change_pct is also returned when previous != 0
        - numerator and denominator are returned for both periods
        - experimental classification distinguishes materiality
          from statistical evidence

    For non-rate KPIs:
        - absolute_delta is current - previous
        - relative_change_pct is the percentage change when
          previous != 0

    The legacy change_pct field is preserved as an alias for
    relative_change_pct.

    If previous == 0, relative percentage change is None rather
    than producing an undefined or infinite result.

    When config is supplied, materiality is evaluated using the
    configured deterministic thresholds.
    """

    if window_days < 1:
        raise ValueError(
            "window_days must be greater than or equal to 1"
        )

    latest = _latest_date(
        view,
        engine=engine,
    )

    if latest is None:
        return None

    current_end = latest
    current_start = (
        latest - timedelta(days=window_days - 1)
    )

    previous_end = current_start - timedelta(days=1)
    previous_start = (
        previous_end - timedelta(days=window_days - 1)
    )

    current = _aggregate_period(
        aggregation,
        column,
        view,
        current_start,
        current_end,
        engine=engine,
    )

    previous = _aggregate_period(
        aggregation,
        column,
        view,
        previous_start,
        previous_end,
        engine=engine,
    )

    if current is None or previous is None:
        return None

    absolute_delta = current - previous

    if previous == 0:
        relative_change_pct = None
    else:
        relative_change_pct = (
            (absolute_delta / previous) * 100
        )

    percentage_point_change = None

    if metric_type == "rate":
        percentage_point_change = (
            absolute_delta * 100
        )

    if relative_change_pct is None:
        direction_value = absolute_delta
    else:
        direction_value = relative_change_pct

    if abs(direction_value) < 1:
        direction = "Stable"
    elif direction_value > 0:
        direction = "Increase"
    else:
        direction = "Decrease"

    current_n = _count_period_rows(
        view,
        current_start,
        current_end,
        engine=engine,
    )

    previous_n = _count_period_rows(
        view,
        previous_start,
        previous_end,
        engine=engine,
    )

    current_numerator = None
    previous_numerator = None

    if metric_type == "rate":
        current_numerator = _aggregate_period(
            "SUM",
            column,
            view,
            current_start,
            current_end,
            engine=engine,
        )

        previous_numerator = _aggregate_period(
            "SUM",
            column,
            view,
            previous_start,
            previous_end,
            engine=engine,
        )

    materiality = None

    if config is not None:
        rules = config.get("materiality", {})

        minimum_n = rules.get(
            "minimum_n",
            30,
        )

        minimum_relative_change_pct = rules.get(
            "minimum_relative_change_pct",
            10.0,
        )

        minimum_rate_change_pp = rules.get(
            "minimum_rate_change_pp",
            1.0,
        )

        significance_level = rules.get(
            "significance_level",
            0.05,
        )

        sufficient_n = (
            current_n >= minimum_n
            and previous_n >= minimum_n
        )

        if metric_type == "rate":
            change_meets_threshold = (
                percentage_point_change is not None
                and abs(percentage_point_change)
                >= minimum_rate_change_pp
            )
        else:
            change_meets_threshold = (
                relative_change_pct is not None
                and abs(relative_change_pct)
                >= minimum_relative_change_pct
            )

        legacy_material = (
            sufficient_n and change_meets_threshold
        )

        p_value = None
        classification = None

        if metric_type == "rate":
            if (
                current_numerator is not None
                and previous_numerator is not None
            ):
                p_value = _two_proportion_p_value(
                    current_numerator,
                    current_n,
                    previous_numerator,
                    previous_n,
                )

            if not change_meets_threshold:
                classification = (
                    "below_materiality_threshold"
                )
            elif (
                sufficient_n
                and p_value is not None
                and p_value < significance_level
            ):
                classification = "material_signal"
            else:
                classification = (
                    "not_statistically_established"
                )

        materiality = {
            "material": legacy_material,
            "classification": classification,
            "sufficient_n": sufficient_n,
            "change_meets_threshold": (
                change_meets_threshold
            ),
            "p_value": (
                round(p_value, 6)
                if p_value is not None
                else None
            ),
            "significance_level": significance_level,
            "minimum_n": minimum_n,
            "minimum_relative_change_pct": (
                minimum_relative_change_pct
            ),
            "minimum_rate_change_pp": (
                minimum_rate_change_pp
            ),
            "assumption_status": rules.get(
                "assumption_status",
                "ASSUMED_CONFIG",
            ),
        }

    rounded_relative_change = (
        round(relative_change_pct, 2)
        if relative_change_pct is not None
        else None
    )

    result = {
        "window": f"Last {window_days} Days",
        "current_start": str(current_start),
        "current_end": str(current_end),
        "previous_start": str(previous_start),
        "previous_end": str(previous_end),
        "current": current,
        "previous": previous,
        "absolute_delta": round(
            absolute_delta,
            6,
        ),
        "relative_change_pct": rounded_relative_change,
        "change_pct": rounded_relative_change,
        "direction": direction,
        "current_n": current_n,
        "previous_n": previous_n,
        "materiality": materiality,
    }

    if metric_type == "rate":
        result["percentage_point_change"] = round(
            percentage_point_change,
            4,
        )
        result["current_numerator"] = current_numerator
        result["current_denominator"] = current_n
        result["previous_numerator"] = previous_numerator
        result["previous_denominator"] = previous_n

    return result
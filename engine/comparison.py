"""
InsightForge Historical Comparison Engine

Provides deterministic period-over-period comparison.

Principles
----------
- Uses dataset dates, never system time.
- Current period is anchored to MAX(Date).
- Returns None when insufficient history exists.
- Performs arithmetic only.
- Does not generate business narratives.
"""

from datetime import timedelta
from datetime import date
from sqlalchemy import text

from engine.db import get_engine

def _latest_date(view: str) -> date:
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

    with get_engine().connect() as connection:
        latest = connection.execute(sql).scalar()

    return latest

def _aggregate_period(
    aggregation: str,
    column: str,
    view: str,
    start_date,
    end_date,
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

    with get_engine().connect() as connection:

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

def compare_periods(
    aggregation: str,
    column: str,
    view: str,
    window_days: int = 7,
) -> dict | None:
    """
    Compare the latest reporting window against the previous window.
    """

    latest = _latest_date(view)

    current_end = latest
    current_start = latest - timedelta(days=window_days - 1)

    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=window_days - 1)

    current = _aggregate_period(
        aggregation,
        column,
        view,
        current_start,
        current_end,
    )

    previous = _aggregate_period(
        aggregation,
        column,
        view,
        previous_start,
        previous_end,
    )

    if current is None or previous is None or previous == 0:
        return None

    change_pct = ((current - previous) / previous) * 100

    if abs(change_pct) < 1:
        direction = "Stable"
    elif change_pct > 0:
        direction = "Increase"
    else:
        direction = "Decrease"

    return {
        "window": f"Last {window_days} Days",
        "current": current,
        "previous": previous,
        "change_pct": round(change_pct, 2),
        "direction": direction,
    }
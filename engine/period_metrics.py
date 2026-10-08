"""
Deterministic period KPI calculations.

Calculates semantic KPI values for explicit reporting windows.

No LLM.
No business narrative.
No causal interpretation.
"""

from datetime import date

from sqlalchemy import text

from engine.db import get_engine


def _execute_scalar(
    sql: str,
    params: dict,
):
    """Execute a scalar SQL query."""

    with get_engine().connect() as connection:
        return connection.execute(
            text(sql),
            params,
        ).scalar()


def period_kpi_value(
    metric_name: str,
    source: str,
    start_date: date,
    end_date: date,
    config: dict,
) -> float | None:
    """
    Calculate a semantic KPI for an explicit reporting period.

    Supported KPI types:
        count
        count_distinct
        sum
        average
        rate

    Also supports the Telecom calculated KPI:
        cost_per_incident

    The calculation follows the KPI definition rather than blindly
    aggregating a physical column.
    """

    kpi_config = config["kpis"].get(metric_name)

    if kpi_config is None:
        raise ValueError(
            f"KPI '{metric_name}' is not configured."
        )

    kpi_type = kpi_config["type"]

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    date_column = config["dataset"]["date_column"]

    date_filter = (
        f"{date_column} BETWEEN :start_date AND :end_date"
    )

    if metric_name == "cost_per_incident":

        cost_column = config["kpis"]["total_cost"]["column"]

        cost_sql = f"""
            SELECT SUM({cost_column})
            FROM {source}
            WHERE {date_filter}
        """

        incident_sql = f"""
            SELECT COUNT(*)
            FROM {source}
            WHERE {date_filter}
        """

        total_cost = _execute_scalar(
            cost_sql,
            params,
        )

        incident_count = _execute_scalar(
            incident_sql,
            params,
        )

        if total_cost is None or not incident_count:
            return None

        return float(total_cost) / float(incident_count)

    if kpi_type == "count":

        expression = "COUNT(*)"

    elif kpi_type == "count_distinct":

        expression = (
            f"COUNT(DISTINCT {kpi_config['column']})"
        )

    elif kpi_type == "sum":

        expression = f"SUM({kpi_config['column']})"

    elif kpi_type == "average":

        expression = f"AVG({kpi_config['column']})"

    elif kpi_type == "rate":

        expression = f"AVG({kpi_config['column']})"

    else:

        raise ValueError(
            f"Unsupported period KPI type: {kpi_type}"
        )

    sql = f"""
        SELECT {expression}
        FROM {source}
        WHERE {date_filter}
    """

    result = _execute_scalar(
        sql,
        params,
    )

    if result is None:
        return None

    return float(result)

def cost_bridge_periods(
    source: str,
    previous_start: date,
    previous_end: date,
    current_start: date,
    current_end: date,
    config: dict,
) -> dict | None:
    """
    Build the deterministic Total Cost bridge between two periods.

    Total Cost = Incident Count × Cost per Incident.

    The returned bridge is a mathematical decomposition only.
    It does not establish business causality.
    """

    from engine.bridge import bridge_from_periods

    previous_volume = period_kpi_value(
        metric_name="incident_count",
        source=source,
        start_date=previous_start,
        end_date=previous_end,
        config=config,
    )

    current_volume = period_kpi_value(
        metric_name="incident_count",
        source=source,
        start_date=current_start,
        end_date=current_end,
        config=config,
    )

    previous_rate = period_kpi_value(
        metric_name="cost_per_incident",
        source=source,
        start_date=previous_start,
        end_date=previous_end,
        config=config,
    )

    current_rate = period_kpi_value(
        metric_name="cost_per_incident",
        source=source,
        start_date=current_start,
        end_date=current_end,
        config=config,
    )

    if any(
        value is None
        for value in (
            previous_volume,
            current_volume,
            previous_rate,
            current_rate,
        )
    ):
        return None

    return bridge_from_periods(
        previous_volume=previous_volume,
        current_volume=current_volume,
        previous_rate=previous_rate,
        current_rate=current_rate,
    )
"""
Computes one verified business metric per call.

The analytics engine performs deterministic SQL aggregation.
No business narratives are generated here.
"""

from sqlalchemy import text

from engine.db import get_engine

SQL_TEMPLATES = {
    "count": "SELECT COUNT(*) AS value FROM {source}",
    "sum": "SELECT SUM({column}) AS value FROM {source}",
    "average": "SELECT AVG({column}) AS value FROM {source}",
    "rate": "SELECT AVG({column}) AS value FROM {source}",
}


def calculate_metric(metric_name: str, config: dict) -> float | None:
    """
    Calculate one KPI defined in the semantic configuration.
    """

    kpi = config["kpis"].get(metric_name)

    if kpi is None:
        raise ValueError(f"Unknown KPI: '{metric_name}'")

    # ----------------------------
    # Calculated KPIs
    # ----------------------------
    if kpi["type"] == "calculated":

        if metric_name == "cost_per_incident":

            total_cost = calculate_metric(
                "total_cost",
                config,
            )

            incident_count = calculate_metric(
                "incident_count",
                config,
            )

            if incident_count == 0:
                return None

            return total_cost / incident_count

        formula = kpi.get("formula")

        if formula:

            numerator, denominator = [
            part.strip()
            for part in formula.split("/")
        ]
        if numerator == config["dataset"]["grain_column"]:
          numerator_sql = f"COUNT({numerator})"
        else:
          numerator_sql = f"SUM({numerator})"

        if denominator == config["dataset"]["grain_column"]:
          denominator_sql = f"COUNT({denominator})"
        else:
          denominator_sql = f"SUM({denominator})"


        sql = f"""
            SELECT
                {numerator_sql} /
                NULLIF({denominator_sql}, 0)
            FROM {config["database"]["view"]}
        """

        with get_engine().connect() as connection:
            result = connection.execute(text(sql)).scalar()

        return float(result)

        raise ValueError(
            f"Unknown calculated KPI: '{metric_name}'"
        )

    # ----------------------------
    # SQL KPIs
    # ----------------------------
    template = SQL_TEMPLATES[kpi["type"]]

    sql = template.format(
        source=config["database"]["view"],
        column=kpi.get("column", ""),
    )

    with get_engine().connect() as connection:
        result = connection.execute(text(sql)).scalar()

    return float(result) if result is not None else None
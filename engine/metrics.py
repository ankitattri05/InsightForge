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

    template = SQL_TEMPLATES[kpi["type"]]

    sql = template.format(
        source=config["database"]["view"],
        column=kpi.get("column", "")
    )

    with get_engine().connect() as connection:
        result = connection.execute(text(sql)).scalar()

    return float(result) if result is not None else None
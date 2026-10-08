"""
Computes one verified business metric per call.

The analytics engine performs deterministic SQL aggregation.
No business narratives are generated here.
"""

from sqlalchemy import text

from engine.db import get_engine, get_source


SQL_TEMPLATES = {
    "count": "SELECT COUNT(*) AS value FROM {source}",
    "count_distinct": (
        "SELECT COUNT(DISTINCT {column}) AS value FROM {source}"
    ),
    "sum": "SELECT SUM({column}) AS value FROM {source}",
    "average": "SELECT AVG({column}) AS value FROM {source}",
    "rate": "SELECT AVG({column}) AS value FROM {source}",
}


def _build_formula_aggregation(
    kpi_name: str,
    kpi_config: dict,
    metric_name: str,
    side: str,
) -> str:
    """
    Resolve a calculated-KPI operand using the referenced KPI's
    declared semantic aggregation.
    """

    if kpi_config is None:
        raise ValueError(
            f"Unknown KPI reference '{kpi_name}' "
            f"in calculated KPI '{metric_name}'"
        )

    kpi_type = kpi_config["type"]

    if kpi_type == "count_distinct":
        return f"COUNT(DISTINCT {kpi_config['column']})"

    if kpi_type == "count":
        return "COUNT(*)"

    if kpi_type == "sum":
        return f"SUM({kpi_config['column']})"

    if kpi_type == "average":
        return f"AVG({kpi_config['column']})"

    if kpi_type == "rate":
        return f"AVG({kpi_config['column']})"

    raise ValueError(
        f"Unsupported KPI type '{kpi_type}' for {side} operand "
        f"'{kpi_name}' in calculated KPI '{metric_name}'"
    )


def _build_calculated_sql(
    metric_name: str,
    kpi: dict,
    config: dict,
    source: str,
) -> str:
    """
    Build deterministic SQL for a calculated KPI.

    Calculated KPI formulas reference KPI names rather than raw
    database columns so that aggregation semantics remain explicit.
    """

    formula = kpi.get("formula")

    if not formula:
        raise ValueError(
            f"Unknown calculated KPI: '{metric_name}'"
        )

    parts = formula.split("/")

    if len(parts) != 2:
        raise ValueError(
            f"Unsupported formula for calculated KPI "
            f"'{metric_name}': '{formula}'"
        )

    numerator, denominator = [
        part.strip()
        for part in parts
    ]

    numerator_kpi = config["kpis"].get(numerator)
    denominator_kpi = config["kpis"].get(denominator)

    numerator_sql = _build_formula_aggregation(
        numerator,
        numerator_kpi,
        metric_name,
        "numerator",
    )

    denominator_sql = _build_formula_aggregation(
        denominator,
        denominator_kpi,
        metric_name,
        "denominator",
    )

    return f"""
        SELECT
            {numerator_sql} /
            NULLIF({denominator_sql}, 0)
        FROM {source}
    """


def calculate_metric(
    metric_name: str,
    config: dict,
) -> float | None:
    """
    Calculate one KPI defined in the semantic configuration.
    """

    kpi = config["kpis"].get(metric_name)

    if kpi is None:
        raise ValueError(f"Unknown KPI: '{metric_name}'")

    source = get_source(config)

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

            if incident_count in (None, 0):
                return None

            return total_cost / incident_count

        sql = _build_calculated_sql(
            metric_name,
            kpi,
            config,
            source,
        )

        with get_engine().connect() as connection:
            result = connection.execute(
                text(sql)
            ).scalar()

        return float(result) if result is not None else None

    # ----------------------------
    # SQL KPIs
    # ----------------------------
    template = SQL_TEMPLATES[kpi["type"]]

    sql = template.format(
        source=source,
        column=kpi.get("column", ""),
    )

    with get_engine().connect() as connection:
        result = connection.execute(
            text(sql)
        ).scalar()

    return float(result) if result is not None else None


def calculate_metric_with_evidence(
    metric_name: str,
    config: dict,
) -> dict:
    """
    Calculate one KPI and return its deterministic evidence.

    The existing calculate_metric() contract is preserved.
    """

    kpi = config["kpis"].get(metric_name)

    if kpi is None:
        raise ValueError(f"Unknown KPI: '{metric_name}'")

    source = get_source(config)

    # ----------------------------
    # Calculated KPI:
    # cost_per_incident
    # ----------------------------
    if metric_name == "cost_per_incident":

        total_cost = calculate_metric_with_evidence(
            "total_cost",
            config,
        )

        incident_count = calculate_metric_with_evidence(
            "incident_count",
            config,
        )

        if incident_count["value"] in (None, 0):
            return {
                "value": None,
                "evidence": [],
            }

        value = (
            total_cost["value"]
            / incident_count["value"]
        )

        return {
            "value": value,
            "evidence": (
                total_cost["evidence"]
                + incident_count["evidence"]
            ),
        }

    # ----------------------------
    # Other calculated KPIs
    # ----------------------------
    if kpi["type"] == "calculated":

        sql = _build_calculated_sql(
            metric_name,
            kpi,
            config,
            source,
        )

        with get_engine().connect() as connection:
            result = connection.execute(
                text(sql)
            ).scalar()

        value = float(result) if result is not None else None

        return {
            "value": value,
            "evidence": [
                {
                    "source_query_id": f"kpi:{metric_name}",
                    "source_view": source,
                    "sql": sql.strip(),
                }
            ],
        }

    # ----------------------------
    # SQL KPI
    # ----------------------------
    template = SQL_TEMPLATES[kpi["type"]]

    sql = template.format(
        source=source,
        column=kpi.get("column", ""),
    )

    with get_engine().connect() as connection:
        result = connection.execute(
            text(sql)
        ).scalar()

    value = float(result) if result is not None else None

    return {
        "value": value,
        "evidence": [
            {
                "source_query_id": f"kpi:{metric_name}",
                "source_view": source,
                "sql": sql.strip(),
            }
        ],
    }
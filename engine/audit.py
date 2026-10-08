"""
Deterministic dataset structure and KPI semantic audits.

This module audits the structural and semantic integrity of
configured datasets.

It does not generate business interpretations, recommendations,
or narratives.
"""

from sqlalchemy import text

from engine.db import get_engine, get_source


def _execute_scalar(sql: str):
    """Execute SQL that returns a single scalar value."""

    with get_engine().connect() as connection:
        return connection.execute(text(sql)).scalar()


def _audit_grain(config: dict, source: str) -> dict:
    """
    Audit whether the physical dataset matches its declared grain.
    """

    grain_column = config["dataset"]["grain_column"]

    row_count_sql = f"""
        SELECT COUNT(*)
        FROM {source}
    """

    distinct_grain_sql = f"""
        SELECT COUNT(DISTINCT {grain_column})
        FROM {source}
    """

    row_count = int(
        _execute_scalar(row_count_sql) or 0
    )

    distinct_grain_count = int(
        _execute_scalar(distinct_grain_sql) or 0
    )

    duplicate_grain_count = (
        row_count - distinct_grain_count
    )

    return {
        "grain_column": grain_column,
        "row_count": row_count,
        "distinct_grain_count": distinct_grain_count,
        "duplicate_grain_count": duplicate_grain_count,
        "grain_unique": (
            row_count == distinct_grain_count
        ),
    }


def _audit_null_dimensions(
    config: dict,
    source: str,
) -> dict:
    """
    Audit configured dimensions for NULL members.
    """

    results = {}

    for dimension in config["dimensions"]:

        sql = f"""
            SELECT COUNT(*)
            FROM {source}
            WHERE {dimension} IS NULL
        """

        null_count = int(
            _execute_scalar(sql) or 0
        )

        results[dimension] = {
            "null_count": null_count,
            "has_nulls": null_count > 0,
        }

    return results


def _aggregation_expression(
    kpi_config: dict,
) -> str | None:
    """
    Translate a KPI definition into its deterministic SQL aggregation.
    """

    kpi_type = kpi_config["type"]

    if kpi_type == "sum":
        return f"SUM({kpi_config['column']})"

    if kpi_type == "count":
        return "COUNT(*)"

    if kpi_type == "count_distinct":
        return (
            f"COUNT(DISTINCT {kpi_config['column']})"
        )

    return None


def _audit_kpi_additivity(
    metric_name: str,
    kpi_config: dict,
    config: dict,
    source: str,
) -> dict:
    """
    Determine the dimensions across which a KPI reconciles.
    """

    kpi_type = kpi_config["type"]

    if kpi_type in {
        "average",
        "rate",
        "calculated",
    }:
        return {
            "type": kpi_type,
            "additive_across": [],
            "reason": "Non-additive KPI type",
        }

    if kpi_type == "count_distinct":
        return {
            "type": kpi_type,
            "additive_across": [],
            "reason": (
                "Distinct counts are not additive across dimensions "
                "because the same entity may appear in multiple groups."
            ),
        }

    expression = _aggregation_expression(
        kpi_config
    )

    if expression is None:
        return {
            "type": kpi_type,
            "additive_across": [],
            "reason": "Unsupported KPI aggregation",
        }

    total_sql = f"""
        SELECT {expression}
        FROM {source}
    """

    total = _execute_scalar(total_sql)

    if total is None:
        return {
            "type": kpi_type,
            "additive_across": [],
            "reason": "No total value available",
        }

    total = float(total)

    additive_across = []

    for dimension in config["dimensions"]:

        grouped_sql = f"""
            SELECT
                {dimension} AS dimension_value,
                {expression} AS value
            FROM {source}
            GROUP BY {dimension}
        """

        with get_engine().connect() as connection:
            rows = connection.execute(
                text(grouped_sql)
            ).mappings().all()

        grouped_total = sum(
            float(row["value"])
            for row in rows
            if row["value"] is not None
        )

        if abs(grouped_total - total) <= 1e-6:
            additive_across.append(dimension)

    return {
        "type": kpi_type,
        "additive_across": additive_across,
        "reason": None,
    }


def _audit_grain_level_measures(
    config: dict,
    source: str,
) -> dict:
    """
    Detect measures that are constant within the declared grain.

    A measure that is repeated with the same value across multiple
    physical rows for the same grain entity is potentially an
    entity-level attribute stored in a lower-grain dataset.

    This does not declare the measure invalid. It exposes the
    semantic property so downstream KPI definitions can account
    for the actual grain.
    """

    grain_column = config["dataset"]["grain_column"]

    results = {}

    for measure in config["measures"]:

        sql = f"""
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT {grain_column}) AS grain_count,
                COUNT(DISTINCT {measure}) AS distinct_measure_count
            FROM {source}
            WHERE {measure} IS NOT NULL
        """

        with get_engine().connect() as connection:
            row = connection.execute(
                text(sql)
            ).mappings().one()

        row_count = int(row["row_count"] or 0)
        grain_count = int(row["grain_count"] or 0)
        distinct_measure_count = int(
            row["distinct_measure_count"] or 0
        )

        if row_count == 0:
            results[measure] = {
                "grain_level_constant": False,
                "reason": "No non-null values",
            }
            continue

        consistency_sql = f"""
            SELECT COUNT(*)
            FROM (
                SELECT
                    {grain_column}
                FROM {source}
                WHERE {measure} IS NOT NULL
                GROUP BY {grain_column}
                HAVING COUNT(DISTINCT {measure}) > 1
            ) AS inconsistent
        """

        inconsistent_grains = int(
            _execute_scalar(consistency_sql) or 0
        )

        grain_level_constant = (
            inconsistent_grains == 0
            and row_count > grain_count
        )

        results[measure] = {
            "grain_level_constant": grain_level_constant,
            "row_count": row_count,
            "grain_count": grain_count,
            "distinct_measure_count": distinct_measure_count,
            "inconsistent_grains": inconsistent_grains,
        }

    return results


def audit_dataset(config: dict) -> dict:
    """
    Run structural and semantic audits for one configured dataset.
    """

    source = get_source(config)

    grain = _audit_grain(
        config,
        source,
    )

    null_dimensions = _audit_null_dimensions(
        config,
        source,
    )

    kpis = {}

    for metric_name, kpi_config in config["kpis"].items():

        kpis[metric_name] = _audit_kpi_additivity(
            metric_name,
            kpi_config,
            config,
            source,
        )

    grain_level_measures = _audit_grain_level_measures(
        config,
        source,
    )

    return {
        "source": source,
        "dataset": grain,
        "dimensions": null_dimensions,
        "grain_level_measures": grain_level_measures,
        "kpis": kpis,
    }
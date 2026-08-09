"""
Validates deterministic KPI calculations against approved ground-truth values.

Never computes business metrics itself — only compares what the analytics
engine produced against known-correct figures (SQL output, BRD, Power BI).

Any failure to compute a metric becomes a structured validation result so
that a batch validation always completes and reports every KPI.
"""

from math import isclose

from engine.metrics import calculate_metric


def validate_metric(
    metric_name: str,
    expected_value: float,
    config: dict,
    *,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-9,
) -> dict:
    """
    Validate one KPI against an expected ground-truth value.
    """

    try:
        actual_value = calculate_metric(metric_name, config)

    except Exception as error:
        return {
            "metric": metric_name,
            "expected": expected_value,
            "actual": None,
            "passed": False,
            "reason": f"Calculation failed: {error}",
        }

    if actual_value is None:
        return {
            "metric": metric_name,
            "expected": expected_value,
            "actual": None,
            "passed": False,
            "reason": "No data returned",
        }

    passed = isclose(
        actual_value,
        expected_value,
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    )

    return {
        "metric": metric_name,
        "expected": expected_value,
        "actual": actual_value,
        "passed": passed,
        "reason": None if passed else "Value does not match ground truth",
    }


def validate_metrics(
    expected_metrics: dict[str, float],
    config: dict,
) -> list[dict]:
    """
    Validate multiple KPIs.

    Parameters
    ----------
    expected_metrics
        Example:

        {
            "incident_count": 25000,
            "total_cost": 3103613147.0,
            "sla_breach_rate": 0.0999
        }
    """

    return [
        validate_metric(metric_name, expected_value, config)
        for metric_name, expected_value in expected_metrics.items()
    ]
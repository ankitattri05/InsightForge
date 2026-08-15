"""
Deterministic business findings.

Converts verified KPIs into business findings using
configuration-driven business rules.

No SQL.
No LLM.
No AI.
"""

from engine.config_loader import load_config


def evaluate_metric(
    metric_name: str,
    value: float,
    config: dict,
) -> dict:
    """
    Evaluate one KPI against configured thresholds.
    """

    thresholds = config.get("thresholds", {}).get(metric_name)

    if thresholds is None:
        return {
            "metric": metric_name,
            "value": value,
            "status": "Not Configured",
            "finding": "No business rule defined."
        }

    direction = thresholds["direction"]

    if direction == "lower_is_better":

        if value <= thresholds["good"]:
            status = "Good"

        elif value <= thresholds["warning"]:
            status = "Warning"

        else:
            status = "Critical"

    else:
        raise ValueError(
            f"Unsupported threshold direction: {direction}"
        )

    return {
        "metric": metric_name,
        "value": value,
        "status": status,
        "finding": (
            f"{metric_name} is currently classified as {status}."
        ),
    }
def evaluate_metrics(
    metrics: dict[str, float],
    config: dict,
) -> list[dict]:
    """
    Evaluate multiple KPIs using configured business rules.
    """

    return [
        evaluate_metric(
            metric_name,
            value,
            config,
        )
        for metric_name, value in metrics.items()
    ]
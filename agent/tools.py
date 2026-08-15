"""
The only bridge between the LLM and the analytics engine.

Validation is performed once during initialization.
After successful validation, only verified metrics can be exposed
to the LLM.
"""

from typing import Optional, TypedDict
from engine.interpreter_telecom import interpret_metric
from engine.interpreter_retail import interpret_retail_metric

from engine.config_loader import load_config
from engine.metrics import calculate_metric
from engine.validation import validate_metrics

_config: Optional[dict] = None
_validation_passed = False


class ToolResult(TypedDict):
    success: bool
    data: Optional[dict]
    error: Optional[str]


def initialize(
    config_path: str,
    expected_metrics: dict[str, float],
) -> None:
    """
    Load configuration and verify all ground-truth metrics.

    The agent refuses to start if validation fails.
    """

    global _config
    global _validation_passed

    _config = load_config(config_path)

    failures = [
        result
        for result in validate_metrics(expected_metrics, _config)
        if not result["passed"]
    ]

    if failures:
        from pprint import pprint

        pprint(failures)
        raise RuntimeError("Startup validation failed.")

    _validation_passed = True

def get_config() -> dict:
    """
    Return the loaded project configuration.
    """
    return _config

def _require_validation() -> None:
    """
    Ensure initialization completed successfully.
    """

    if not _validation_passed:
        raise RuntimeError(
            "tools.initialize() has not completed successfully."
        )


def get_metric(metric_name: str) -> ToolResult:
    """
    Return one verified business metric.
    """

    _require_validation()

    try:
        value = calculate_metric(metric_name, _config)

    except Exception as e:
        return {
        "success": False,
        "data": None,
        "error": str(e),
    }

    if value is None:
        return {
            "success": False,
            "data": None,
            "error": "No data available for this KPI.",
        }

    project = _config["project"]["name"]

    if project == "Telecom Service Assurance":
        finding = interpret_metric(
            metric_name,
            value,
            _config,
        )
    else:
        finding = interpret_retail_metric(
            metric_name,
            value,
            _config,
    )

    return {
        "success": True,
        "data": {
            "metric": metric_name,
            "value": value,
            "display_value": _format_metric(metric_name, value),
            "finding": finding,
        },
        "error": None,
    }


def get_metrics(
    metric_names: list[str],
) -> list[ToolResult]:
    """
    Return multiple verified business metrics.
    """

    return [
        get_metric(metric_name)
        for metric_name in metric_names
    ]

def get_config() -> dict:
    """
    Return the active semantic configuration.
    """
    return _config

def _format_metric(
    metric_name: str,
    value: float,
) -> str:
    """
    Return a deterministic display string for a KPI.
    """

    if metric_name in {
        "incident_count",
        "customers_impacted",
        "orders",
        "quantity",
    }:
        return f"{value:,.0f}"

    if metric_name in {
        "sla_breach_rate",
        "profit_margin",
    }:
        return f"{value:.2%}"

    if metric_name == "avg_resolution_time":
        return f"{value:.2f} minutes"

    if metric_name == "avg_shipping_days":
        return f"{value:.2f} days"

    if metric_name in {
        "total_cost",
        "dispatch_cost",
        "cost_per_incident",
        "sales",
        "profit",
        "shipping_cost",
        "average_order_value",
    }:
         return f"₹{value:,.2f}"

    return str(value)
"""
The only bridge between the LLM and the analytics engine.

Validation is performed once during initialization.
After successful validation, only verified metrics can be exposed
to the LLM.
"""

from typing import Optional, TypedDict

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
        raise RuntimeError(
            f"Startup validation failed: {failures}"
        )

    _validation_passed = True


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

    except ValueError:
        return {
            "success": False,
            "data": None,
            "error": f"Unknown KPI: '{metric_name}'",
        }

    if value is None:
        return {
            "success": False,
            "data": None,
            "error": "No data available for this KPI.",
        }

    return {
        "success": True,
        "data": {
            "metric": metric_name,
            "value": value,
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
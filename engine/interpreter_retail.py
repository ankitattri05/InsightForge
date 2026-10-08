"""
Deterministic business interpretation layer.

Transforms verified KPI values into verified business findings.

No LLM logic belongs here.
"""

from typing import TypedDict

from sqlalchemy import text

from engine.comparison import compare_periods
from engine.db import get_engine, get_source
from engine.diagnostics import retail_diagnostics


class Finding(TypedDict, total=False):
    finding_id: str
    metric: str
    value: float
    unit: str
    definition: str
    n: int
    additive: bool
    additive_across: list[str]
    evidence_class: str
    not_established: list[str]
    status: str
    headline: str
    business_meaning: str
    interpretation: str
    diagnostics: dict
    comparison: dict | None


def _row_count(source: str) -> int:
    """Return the number of physical rows supporting the finding."""

    sql = text(
        f"""
        SELECT COUNT(*)
        FROM {source}
        """
    )

    with get_engine().connect() as connection:
        return int(connection.execute(sql).scalar() or 0)


def _base_finding(
    metric_name: str,
    value: float,
    config: dict,
    *,
    unit: str,
    definition: str,
    additive: bool,
    evidence_class: str,
    not_established: list[str],
) -> dict:
    """
    Build deterministic G1 finding metadata.

    The metadata defines what the KPI means and the boundaries of
    what can be concluded from it. The LLM does not define these.
    """

    source = get_source(config)

    return {
        "finding_id": f"retail:{metric_name}",
        "metric": metric_name,
        "value": value,
        "unit": unit,
        "definition": definition,
        "n": _row_count(source),
        "additive": additive,
        "evidence_class": evidence_class,
        "not_established": not_established,
    }


def interpret_retail_metric(
    metric_name: str,
    value: float,
    config: dict,
) -> Finding:

    source = get_source(config)

    if metric_name == "sales":

        diagnostics = retail_diagnostics(
            view=source,
            currency="$",
        )

        diagnostics["top_sales_market"] = (
            diagnostics["top_sales_market"][:3]
        )
        diagnostics["top_profit_category"] = (
            diagnostics["top_profit_category"][:3]
        )
        diagnostics["bottom_profit_subcategory"] = (
            diagnostics["bottom_profit_subcategory"][:3]
        )
        diagnostics["top_shipping_cost_ship_mode"] = (
            diagnostics["top_shipping_cost_ship_mode"][:3]
        )

        bottom_subcategory = (
            diagnostics["bottom_profit_subcategory"][0]
        )

        headline = (
            f"Lowest Profit Subcategory: "
            f"{bottom_subcategory['category']} "
            f"({bottom_subcategory['display']})"
        )

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="configured currency",
            definition=(
                "Sum of sales across all rows in the reporting dataset."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether sales performance is good or bad.",
                "Does not establish profitability.",
                "Does not establish the cause of sales changes.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "headline": headline,
                "diagnostics": diagnostics,
                "business_meaning":
                    "Total sales revenue generated during the reporting period.",
                "interpretation":
                    "Total Sales is a scale-dependent business metric. "
                    "It should be interpreted using historical trends "
                    "and period-over-period comparison rather than fixed thresholds.",
            }
        )

        return finding

    if metric_name == "profit":

        diagnostics = retail_diagnostics(
            view=source,
            currency="$",
        )

        diagnostics["top_profit_category"] = (
            diagnostics["top_profit_category"][:3]
        )
        diagnostics["bottom_profit_subcategory"] = (
            diagnostics["bottom_profit_subcategory"][:3]
        )
        diagnostics["profit_at_risk_concentration"] = (
            diagnostics["profit_at_risk_concentration"][:3]
        )

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="configured currency",
            definition=(
                "Sum of profit across all rows in the reporting dataset."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether profitability is good or bad.",
                "Does not establish the cause of profit changes.",
                "Does not establish future profitability.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total profit generated during the reporting period.",
                "interpretation": (
                    "Total Profit is a scale-dependent business metric. "
                    "The profit-at-risk diagnostic identifies markets where "
                    "30%+ discount losses are disproportionately concentrated "
                    "relative to the market's sales footprint. "
                    "This supports prioritization of disproportionate exposure "
                    "without establishing that discounting caused the loss."
                ),
                "diagnostics": diagnostics,
            }
        )

        return finding

    if metric_name == "orders":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="orders",
            definition=(
                "Count of distinct order_id values in the reporting dataset."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether order volume is good or bad.",
                "Does not establish customer retention or demand causality.",
                "Does not establish future order volume.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total customer orders processed during the reporting period.",
                "interpretation":
                    "Order volume reflects business activity. "
                    "It should be evaluated using historical trends "
                    "and seasonal comparisons rather than fixed thresholds.",
            }
        )

        return finding

    if metric_name == "quantity":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="units",
            definition=(
                "Sum of quantity across all rows in the reporting dataset."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether unit volume is good or bad.",
                "Does not establish the cause of volume changes.",
                "Does not establish future unit demand.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total units sold during the reporting period.",
                "interpretation":
                    "Units Sold represents sales volume. "
                    "It should be evaluated using historical trends, "
                    "product mix, and seasonal comparisons rather than "
                    "fixed thresholds.",
            }
        )

        return finding

    if metric_name == "avg_shipping_days":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="days",
            definition=(
                "Arithmetic mean of time_for_shipping across dataset rows."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether shipping time meets a target.",
                "Does not establish the cause of shipping delays.",
                "Does not establish future delivery performance.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Average shipping time required to deliver customer orders.",
                "interpretation":
                    "Average Shipping Time should be evaluated using "
                    "verified service-level targets and historical trends "
                    "rather than fixed thresholds.",
            }
        )

        return finding

    if metric_name == "shipping_cost":

        diagnostics = retail_diagnostics(
            view=source,
            currency="$",
        )

        diagnostics["top_shipping_cost_ship_mode"] = (
            diagnostics["top_shipping_cost_ship_mode"][:3]
        )

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="configured currency",
            definition=(
                "Sum of shipping_cost across all rows in the reporting dataset."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether shipping cost is efficient.",
                "Does not establish the cause of shipping cost changes.",
                "Does not establish future shipping cost.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total shipping cost incurred during the reporting period.",
                "interpretation":
                    "Shipping Cost is a scale-dependent logistics metric. "
                    "It should be interpreted using historical trends "
                    "and cost-efficiency comparisons rather than fixed thresholds.",
                "diagnostics": diagnostics,
            }
        )

        return finding

    if metric_name == "profit_margin":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="rate",
            definition=(
                "Total profit divided by total sales for the reporting dataset."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether the margin is good or bad without a benchmark.",
                "Does not establish the cause of margin changes.",
                "Does not establish future profitability.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Overall percentage of sales retained as profit.",
                "interpretation":
                    "Profit Margin is reported descriptively. "
                    "Evaluation requires historical comparison or "
                    "verified target benchmarks.",
                "diagnostics": None,
                "comparison": None,
            }
        )

        return finding

    if metric_name == "average_order_value":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="configured currency per order",
            definition=(
                "Total sales divided by the count of distinct orders."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether order value is good or bad without a benchmark.",
                "Does not establish the cause of order-value changes.",
                "Does not establish future order value.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Average revenue generated per customer order.",
                "interpretation":
                    "Average Order Value is reported descriptively. "
                    "Evaluation requires historical comparison or "
                    "verified target benchmarks.",
                "diagnostics": None,
                "comparison": None,
            }
        )

        return finding

    raise ValueError(
        f"No business interpretation defined for '{metric_name}'."
    )

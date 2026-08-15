"""
Deterministic business interpretation layer.

Transforms verified KPI values into verified business findings.

No LLM logic belongs here.
"""

from engine.diagnostics import retail_diagnostics

from engine.diagnostics import multi_diagnostics
from engine.comparison import compare_periods
from typing import TypedDict


class Finding(TypedDict):
    metric: str
    value: float
    status: str
    business_meaning: str
    interpretation: str


def interpret_retail_metric(
    metric_name: str,
    value: float,
    config: dict,
) -> Finding:

    if metric_name == "incident_count":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Total incidents handled during the reporting period.",
            "interpretation":
                "Incident Count is workload volume. It should not be "
                "classified using fixed thresholds because workload "
                "depends on historical operating baseline."
        }

    if metric_name == "sla_breach_rate":

        thresholds = config["thresholds"]["sla_breach_rate"]
        comparison = compare_periods(
            aggregation="AVG",
            column="SLA_Breach_Flag",
            view=config["database"]["view"],
)
        if value <= thresholds["good"]:
            status = "Good"
        elif value <= thresholds["warning"]:
            status = "Warning"
        else:
            status = "Critical"
        diagnostics = multi_diagnostics(
            view=config["database"]["view"],
        )
        return {
        "metric": metric_name,
        "value": value,
        "status": status,
        "diagnostics": diagnostics,
        "business_meaning":
            "Percentage of incidents that breached SLA.",
        "interpretation":
            f"SLA breach rate is {value:.2%}, classified as "
            f"{status} using configured business thresholds.",
             "comparison": comparison,
    }

    if metric_name == "avg_resolution_time":

        return {
        "metric": metric_name,
        "value": value,
        "status": "Descriptive",
        "business_meaning":
            "Average time required to resolve an incident.",
        "interpretation":
            "Average Resolution Time should be compared against "
            "a severity-weighted expected resolution time. "
            "Until that baseline is implemented, this metric is "
            "reported descriptively without Good/Warning/Critical "
            "classification."
    }

    if metric_name == "total_cost":

        return {
        "metric": metric_name,
        "value": value,
        "status": "Descriptive",
        "business_meaning":
            "Total cost incurred to resolve all incidents during the reporting period.",
        "interpretation":
            "Total Cost-to-Serve is a scale-dependent financial metric. "
            "It should not be classified using fixed thresholds. "
            "Business interpretation should rely on derived KPIs such as "
            "Cost per Incident and trend over time."
    }

    if metric_name == "cost_per_incident":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Average cost incurred to resolve one incident.",
            "interpretation":
                "Cost per Incident should be interpreted using trend "
                "comparison rather than fixed thresholds."
        }

    if metric_name == "customers_impacted":

        return {
        "metric": metric_name,
        "value": value,
        "status": "Descriptive",
        "business_meaning":
            "Total customers affected by reported service incidents.",
        "interpretation":
            f"{value:,.0f} customers were impacted during the reporting period. "
            "This metric is reported descriptively, as no verified baseline or "
            "historical comparison is available for performance evaluation."
    }
    
    if metric_name == "dispatch_cost":

     return {
        "metric": metric_name,
        "value": value,
        "status": "Descriptive",
        "business_meaning":
            "Total field dispatch cost incurred to resolve service incidents.",
        "interpretation":
            f"Total dispatch cost was ₹{value:,.2f} during the reporting period. "
            "This metric is reported descriptively, as no verified baseline or "
            "historical comparison is available for performance evaluation."
    }

    if metric_name == "sales":

        diagnostics = retail_diagnostics(
            view=config["database"]["view"],
        )

        headline = (
        f"Lowest Profit Subcategory: "
        f"{diagnostics['bottom_profit_subcategory'][0]['category']} "
        f"({diagnostics['bottom_profit_subcategory'][0]['display']})"
)

        diagnostics["top_sales_market"] = diagnostics["top_sales_market"][:3]
        diagnostics["top_profit_category"] = diagnostics["top_profit_category"][:3]
        diagnostics["bottom_profit_subcategory"] = diagnostics["bottom_profit_subcategory"][:3]
        diagnostics["top_shipping_cost_ship_mode"] = diagnostics["top_shipping_cost_ship_mode"][:3]

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "headline": headline,
            "diagnostics": diagnostics,
            "business_meaning":
                "Total sales revenue generated during the reporting period.",
            "interpretation":
                "Total Sales is a scale-dependent business metric. "
                "It should be interpreted using historical trends "
                "and period-over-period comparison rather than fixed thresholds."
        }

    if metric_name == "profit":

        diagnostics = retail_diagnostics(
            view=config["database"]["view"],
        )

        diagnostics["top_profit_category"] = diagnostics["top_profit_category"][:3]
        diagnostics["bottom_profit_subcategory"] = diagnostics["bottom_profit_subcategory"][:3]

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Total profit generated during the reporting period.",
            "interpretation":
                "Total Profit is a scale-dependent business metric. "
                "It should be interpreted using historical trends "
                "and period-over-period comparison rather than fixed thresholds.",
            "diagnostics": diagnostics,
        }

    if metric_name == "orders":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Total customer orders processed during the reporting period.",
            "interpretation":
                "Order volume reflects business activity. "
                "It should be evaluated using historical trends "
                "and seasonal comparisons rather than fixed thresholds."
        }

    if metric_name == "quantity":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Total units sold during the reporting period.",
            "interpretation":
                "Units Sold represents sales volume. "
                "It should be evaluated using historical trends, "
                "product mix, and seasonal comparisons rather than "
                "fixed thresholds."
        }

    if metric_name == "avg_shipping_days":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
                "Average shipping time required to deliver customer orders.",
            "interpretation":
                "Average Shipping Time should be evaluated using "
                "service-level targets and historical trends rather "
                "than fixed thresholds."
        }

    if metric_name == "shipping_cost":

        diagnostics = retail_diagnostics(
        view=config["database"]["view"],
     )

        diagnostics["top_shipping_cost_ship_mode"] = (
        diagnostics["top_shipping_cost_ship_mode"][:3]
     )

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning":
            "Total shipping cost incurred during the reporting period.",
        "interpretation":
            "Shipping Cost is a scale-dependent logistics metric. "
            "It should be interpreted using historical trends "
            "and cost efficiency comparisons rather than fixed thresholds.",
        "diagnostics": diagnostics,
    }

    if metric_name == "profit_margin":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning": (
                "Overall percentage of sales retained as profit."
            ),
            "interpretation": (
                "Profit margin is reported descriptively. "
                "Evaluation requires historical comparison or target benchmarks."
            ),
            "diagnostics": None,
            "comparison": None,
        }

    if metric_name == "average_order_value":

        return {
            "metric": metric_name,
            "value": value,
            "status": "Descriptive",
            "business_meaning": (
                "Average revenue generated per customer order."
            ),
            "interpretation": (
                "Average order value is reported descriptively. "
                "Evaluation requires historical comparison or target benchmarks."
            ),
            "diagnostics": None,
            "comparison": None,
        }

    raise ValueError(
        f"No business interpretation defined for '{metric_name}'."
    )
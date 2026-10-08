
"""
Deterministic business interpretation layer.

Transforms verified KPI values into verified business findings.

No LLM logic belongs here.
"""

from typing import TypedDict

from engine.comparison import compare_periods
from engine.db import get_engine, get_source
from engine.diagnostics import multi_diagnostics
from engine.period_metrics import cost_bridge_periods


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
    business_meaning: str
    interpretation: str
    diagnostics: dict
    comparison: dict | None
    comparison_interpretation: dict | None
    bridge: dict | None


def _row_count(source: str) -> int:
    """Return the number of physical rows supporting the finding."""

    from sqlalchemy import text

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
    """Build deterministic G1 finding metadata."""

    source = get_source(config)

    return {
        "finding_id": f"telecom:{metric_name}",
        "metric": metric_name,
        "value": value,
        "unit": unit,
        "definition": definition,
        "n": _row_count(source),
        "additive": additive,
        "evidence_class": evidence_class,
        "not_established": not_established,
    }


def _interpret_sla_comparison(
    comparison: dict | None,
) -> dict:
    """Translate SLA comparison results into bounded business language."""

    if comparison is None:
        return {
            "classification": "unavailable",
            "meaning": (
                "No comparable prior period is available. "
                "A trend conclusion cannot be established."
            ),
        }

    materiality = comparison.get("materiality") or {}
    classification = materiality.get("classification")

    meanings = {
        "material_signal": (
            "The observed SLA breach-rate change meets the configured "
            "materiality threshold and is statistically established "
            "under the comparison's assumptions. This does not establish "
            "the operational cause or business impact of the change."
        ),
        "not_statistically_established": (
            "The observed SLA breach-rate change meets the configured "
            "materiality threshold, but the available evidence does not "
            "statistically establish a change. This does not prove that "
            "the underlying rate is unchanged."
        ),
        "below_materiality_threshold": (
            "The observed SLA breach-rate change is below the configured "
            "materiality threshold. This classification alone does not "
            "establish whether the change is statistically significant "
            "or operationally unimportant."
        ),
    }

    return {
        "classification": classification or "unclassified",
        "meaning": meanings.get(
            classification,
            "The comparison is available, but no supported interpretation "
            "is defined for its classification.",
        ),
    }

def _interpret_sla_diagnostics(diagnostics: dict) -> dict:
    """Generate bounded business interpretation from verified diagnostics."""

    top_faults = diagnostics.get("top_fault", [])

    if not top_faults:
        return {
            "status": "unavailable",
            "meaning": "No qualifying fault-category diagnostic is available.",
        }

    top = top_faults[0]

    if not top.get("minimum_n_met", False):
        return {
            "status": "unavailable",
            "meaning": "The leading fault category does not meet the minimum sample requirement.",
        }

    excess_fault = diagnostics.get("excess_breach_fault", [])
    excess_vendor = diagnostics.get("excess_breach_vendor", [])
    excess_state = diagnostics.get("excess_breach_state", [])

    top_excess_fault = excess_fault[0] if excess_fault else None
    top_excess_vendor = excess_vendor[0] if excess_vendor else None
    top_excess_state = excess_state[0] if excess_state else None

    return {
        "status": "priority_for_investigation",
        "category": top["category"],
        "breach_rate": top["value"],
        "overall_rate": top["overall_rate"],
        "excess_vs_overall_pp": top["excess_vs_overall_pp"],
        "incident_count": top["n"],
        "observed_breaches": top["observed_breaches"],
        "benchmark_breaches": top["benchmark_breaches"],
        "excess_breaches": top["excess_breaches"],
        "incident_share": top["incident_share"],
        "breach_share": top["breach_share"],
        "cost": top["cost"],
        "cost_share": top["cost_share"],
        "breach_concentration": top["breach_concentration"],
        "cost_concentration": top["cost_concentration"],
        "excess_breach_fault": excess_fault,
        "excess_breach_vendor": excess_vendor,
        "excess_breach_state": excess_state,
        "meaning": (
            f"{top['category']} has the highest observed SLA breach rate "
            f"among qualifying fault categories at {top['display']}, "
            f"{top['excess_vs_overall_pp']:.2f} percentage points above "
            f"the overall rate. It represents {top['incident_share']:.1%} "
            f"of incidents but approximately {top['breach_share']:.1%} "
            f"of estimated SLA breaches and {top['cost_share']:.1%} "
            f"of total incident cost. Its incident volume is associated "
            f"with {top['breach_concentration']:.2f}x the incident-share "
            f"of estimated SLA breaches and {top['cost_concentration']:.2f}x "
            f"the incident-share of total cost. Its associated incident cost "
            f"is ₹{top['cost']:,.2f}. At the overall breach rate of "
            f"{top['overall_rate']:.2%}, this category would have an "
            f"estimated {top['benchmark_breaches']:.0f} breaches versus "
            f"{top['observed_breaches']:.0f} observed, a difference of "
            f"approximately {top['excess_breaches']:.0f} breaches. "
            f"By excess-breach impact, {top_excess_fault['category']} leads "
            f"fault categories with {top_excess_fault['excess_breaches']:.0f} "
            f"excess breaches, {top_excess_vendor['category']} leads vendors "
            f"with {top_excess_vendor['excess_breaches']:.0f}, and "
            f"{top_excess_state['category']} leads states with "
            f"{top_excess_state['excess_breaches']:.0f}. "
            "This association does not establish root cause or causality."
        ),
    }

def interpret_metric(
    metric_name: str,
    value: float,
    config: dict,
) -> Finding:

    source = get_source(config)

    if metric_name == "incident_count":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="incidents",
            definition=(
                "Count of incident records in the reporting dataset."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether incident volume is good or bad.",
                "Does not establish a performance problem without a verified baseline.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total incidents handled during the reporting period.",
                "interpretation":
                    "Incident Count is workload volume. It should not be "
                    "classified using fixed thresholds because workload "
                    "depends on historical operating baseline.",
            }
        )

        return finding

    if metric_name == "sla_breach_rate":

        thresholds = config["thresholds"]["sla_breach_rate"]

        comparison = compare_periods(
            aggregation="AVG",
            column="SLA_Breach_Flag",
            view=source,
            metric_type="rate",
            config=config,
        )

        comparison_interpretation = _interpret_sla_comparison(
            comparison
        )

        if value <= thresholds["good"]:
            status = "Good"
        elif value <= thresholds["warning"]:
            status = "Warning"
        else:
            status = "Critical"

        diagnostics = multi_diagnostics(
            view=source,
        )
        diagnostic_interpretation = _interpret_sla_diagnostics(diagnostics)

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="rate",
            definition=(
                "Share of incidents where SLA_Breach_Flag equals 1."
            ),
            additive=False,
            evidence_class="benchmark",
            not_established=[
                "Does not establish the root cause of SLA breaches.",
                "Does not establish causality between any diagnostic dimension and breaches.",
                "Does not establish future SLA performance.",
            ],
        )

        finding.update(
            {
                "status": status,
                "diagnostics": diagnostics,
                "business_meaning":
                    "Percentage of incidents that breached SLA.",
                "interpretation":
                    f"SLA breach rate is {value:.2%}, classified as "
                    f"{status} using configured business thresholds.",
                "comparison": comparison,
                "comparison_interpretation": comparison_interpretation,
                "diagnostic_interpretation": diagnostic_interpretation,
            }
        )

        return finding

    if metric_name == "avg_resolution_time":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="minutes",
            definition=(
                "Arithmetic mean of Resolution_Minutes across incidents."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether resolution time is good or bad.",
                "Does not establish a root cause for resolution time.",
                "Does not establish future resolution performance.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Average time required to resolve an incident.",
                "interpretation":
                    "Average Resolution Time should be compared against "
                    "a severity-weighted expected resolution time. "
                    "Until that baseline is implemented, this metric is "
                    "reported descriptively without Good/Warning/Critical "
                    "classification.",
            }
        )

        return finding

    if metric_name == "total_cost":

        comparison = compare_periods(
            aggregation="SUM",
            column="Estimated_Total_Incident_Cost",
            view=source,
            config=config,
        )

        bridge = None

        if comparison is not None:
            bridge = cost_bridge_periods(
                source=source,
                previous_start=comparison["previous_start"],
                previous_end=comparison["previous_end"],
                current_start=comparison["current_start"],
                current_end=comparison["current_end"],
                config=config,
            )
        comparison_interpretation = None

        if comparison is not None:
            comparison_interpretation = {
                "classification": "descriptive_comparison",
                "meaning": (
                    "Total incident cost is compared across two periods. "
                    "The observed change describes cost movement only. "
                    "It does not establish the cause of the change or "
                    "whether cost efficiency improved or worsened."
                ),
            }
        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="INR",
            definition=(
                "Sum of Estimated_Total_Incident_Cost across incidents."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether total cost is efficient.",
                "Does not establish the cause of cost changes.",
                "The volume/rate bridge is a mathematical decomposition, not a causal explanation.",
                "Does not establish future cost.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total cost incurred to resolve all incidents during "
                    "the reporting period.",
                "interpretation":
                    "Total Cost-to-Serve is a scale-dependent financial metric. "
                    "It should not be classified using fixed thresholds. "
                    "Business interpretation should rely on derived KPIs "
                    "such as Cost per Incident and deterministic period "
                    "decomposition.",
                "comparison": comparison,
                "comparison_interpretation": comparison_interpretation,
                "bridge": bridge,
            }
        )

        return finding

    if metric_name == "cost_per_incident":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="INR per incident",
            definition=(
                "Total incident cost divided by total incident count."
            ),
            additive=False,
            evidence_class="descriptive",
            not_established=[
                "Does not establish the cause of cost changes.",
                "Does not establish whether the cost is efficient without a benchmark.",
                "Does not establish future cost performance.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Average cost incurred to resolve one incident.",
                "interpretation":
                    "Cost per Incident should be interpreted using trend "
                    "comparison rather than fixed thresholds.",
            }
        )

        return finding

    if metric_name == "customers_impacted":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="customer impacts",
            definition=(
                "Sum of Customers_Impacted across incident records; "
                "this is not a distinct-customer count."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not represent distinct customers affected.",
                "Does not establish the cause of customer impact.",
                "Does not establish customer-level retention or churn impact.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total customer impacts recorded across service incidents.",
                "interpretation":
                    f"{value:,.0f} customer impacts were recorded during the "
                    "reporting period. This metric is reported descriptively, "
                    "as no verified baseline or historical comparison is "
                    "available for performance evaluation.",
            }
        )

        return finding

    if metric_name == "dispatch_cost":

        finding = _base_finding(
            metric_name,
            value,
            config,
            unit="INR",
            definition=(
                "Sum of Dispatch_Cost across incident records."
            ),
            additive=True,
            evidence_class="descriptive",
            not_established=[
                "Does not establish whether dispatch spending is efficient.",
                "Does not establish the cause of dispatch cost.",
                "Does not establish future dispatch requirements.",
            ],
        )

        finding.update(
            {
                "status": "Descriptive",
                "business_meaning":
                    "Total field dispatch cost incurred to resolve "
                    "service incidents.",
                "interpretation":
                    f"Total dispatch cost was ₹{value:,.2f} during the "
                    "reporting period. This metric is reported "
                    "descriptively, as no verified baseline or historical "
                    "comparison is available for performance evaluation.",
            }
        )

        return finding

    raise ValueError(
        f"No business interpretation defined for '{metric_name}'."
    )

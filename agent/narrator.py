"""
InsightForge Narrator

The only component that communicates with the LLM.

Responsibilities
----------------
- Generate executive narratives from verified business facts.
- Use approved tools only.
- Never calculate metrics.
- Never write SQL.
- Never invent business values.
"""

import json

from engine.diagnostics import reporting_period

from pathlib import Path

from agent.scorecard import generate_scorecard

from anthropic import Anthropic

from agent import tools


_client: Anthropic | None = None
_model: str | None = None
_system_prompt: str | None = None


def initialize(
    api_key: str,
    model_name: str,
    prompt_path: str = "agent/prompts/system_prompt.md",
) -> None:
    """
    Initialize the narrator.
    """

    global _client
    global _model
    global _system_prompt

    _client = Anthropic(api_key=api_key)
    _model = model_name

    _system_prompt = Path(prompt_path).read_text(
        encoding="utf-8"
    )
    
def generate_brief(metric_names: list[str]) -> str:
    """
    Generate an executive business brief using verified metrics.

    Metrics are fetched deterministically by Python.
    The LLM only narrates the returned facts.
    """

    if (
        _client is None
        or _model is None
        or _system_prompt is None
    ):
        raise RuntimeError("Narrator has not been initialized.")

    results = tools.get_metrics(metric_names)
    scorecard = generate_scorecard(
    results,
    tools.get_config(),
)

    failed = [
        result
        for result in results
        if not result["success"]
    ]

    facts = "\n\n".join(
        (
            f"""Metric: {result['data']['metric']}
Value: {result['data']['display_value']}
Status: {result['data']['finding']['status']}
Business Meaning: {result['data']['finding']['business_meaning']}
Interpretation: {result['data']['finding']['interpretation']}
Headline: {result['data']['finding'].get('headline', 'None')}
Diagnostics: {result['data']['finding'].get('diagnostics', {})}
Comparison:
{
    (
        f"""Window: {result['data']['finding']['comparison']['window']}
Previous: {result['data']['finding']['comparison']['previous']:.2%}
Current: {result['data']['finding']['comparison']['current']:.2%}
Direction: {result['data']['finding']['comparison']['direction']}
Change: {result['data']['finding']['comparison']['change_pct']}%"""
    )
    if result["data"]["finding"].get("comparison")
    else "None"
}"""
            if result["success"]
            else f"Unavailable: {result['error']}"
        )
        for result in results
    )

    period = reporting_period(
        view=tools.get_config()["database"]["view"],
        date_column=tools.get_config()["dataset"]["date_column"],
)

    prompt = (
    "Write an executive business summary using ONLY the verified "
    "metrics and deterministic business findings below.\n\n"

    "Report Metadata\n"
    f"Project: {tools.get_config()['project']['name']}\n"
    f"Version: {tools.get_config()['project']['version']}\n"
    f"Reporting Period: {period['start_date']} to {period['end_date']}\n\n"

    "Currency: ₹\n"
    "Format all monetary values in ₹.\n"
    "Never use '$' or any other currency symbol.\n\n"

    "Resolution time is measured in minutes.\n"
    "Always write 'minutes' instead of 'time units'.\n\n"

    f"{facts}"
)

    if failed:
        prompt += (
            "\n\nSome requested metrics were unavailable. "
            "State this explicitly and do not infer missing information."
        )

    response = _client.messages.create(
        model=_model,
        system=_system_prompt,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text_blocks = [
    block.text
    for block in response.content
    if block.type == "text"
]

    brief = "\n".join(text_blocks)
    brief = brief.replace("\n---\n", "\n")

    return f"{scorecard}\n\n{brief}"   
TOOL_SCHEMAS = [
    {
        "name": "get_metric",
    "description": (
        "Return one verified KPI together with its deterministic "
        "business interpretation and any diagnostics attached to it. "
        "Only request KPI names. "
        "Valid KPI names include: "
        "sales, profit, profit_margin, average_order_value, "
        "orders, quantity, avg_shipping_days, shipping_cost. "
        "Never request diagnostic names such as "
        "top_sales_market, top_profit_category, "
        "bottom_profit_subcategory, or "
        "top_shipping_cost_ship_mode because those are returned "
        "inside the KPI diagnostics."
  ),        
        "input_schema": {
            "type": "object",
            "properties": {
                "metric_name": {"type": "string"}
            },
            "required": ["metric_name"],
        },
    },
    {
       "name": "get_metrics",
    "description": (
        "Return multiple verified KPIs. "
        "Only use valid KPI names. "
        "Diagnostics are automatically included with the KPI results. "
        "Never request diagnostic names as metrics."
    ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric_names": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["metric_names"],
        },
    },
]


_TOOL_FUNCTIONS = {
    "get_metric": lambda args: tools.get_metric(args["metric_name"]),
    "get_metrics": lambda args: tools.get_metrics(args["metric_names"]),
}


def answer(question: str) -> str:
    """
    Answer an analytical business question using verified metrics.
    """

    if (
        _client is None
        or _model is None
        or _system_prompt is None
    ):
        raise RuntimeError("Narrator has not been initialized.")

    question_lower = question.lower()
    project = tools.get_config()["project"]["name"]

    # ----------------------------
    # Deterministic KPI routing
    # ----------------------------

    if project == "Retail Sales Analytics":

        if "business performance" in question_lower:
            metric_names = [
                "sales",
                "profit",
                "profit_margin",
                "average_order_value",
                "orders",
                "quantity",
                "avg_shipping_days",
                "shipping_cost",
            ]

        elif "profit margin" in question_lower:
            metric_names = ["profit_margin"]

        elif "shipping cost" in question_lower:
            metric_names = ["shipping_cost"]

        elif "sales" in question_lower:
            metric_names = ["sales"]

        elif (
            "tables" in question_lower
            or "subcategory" in question_lower
            or "lose money" in question_lower
            or "loss" in question_lower
        ):
            metric_names = ["profit"]

        elif "profit" in question_lower:
            metric_names = ["profit"]

        else:
            return "Sorry, I couldn't determine which KPI(s) you are asking about."

    else:

        if (
            "service assurance" in question_lower
            or "business performance" in question_lower
            or "summary" in question_lower
            or "management" in question_lower
            or "focus" in question_lower
            or "priority" in question_lower
        ):
            metric_names = [
                "incident_count",
                "sla_breach_rate",
                "avg_resolution_time",
                "total_cost",
                "dispatch_cost",
                "customers_impacted",
                "cost_per_incident",
            ]

        elif (
            "incident count" in question_lower
            or "total incident" in question_lower
            or "incidents" in question_lower
        ):
            metric_names = ["incident_count"]

        elif (
            "sla" in question_lower
            or "breach" in question_lower
            or "vendor" in question_lower
            or "tejas" in question_lower
            or "zte" in question_lower
            or "nokia" in question_lower
            or "goa" in question_lower
            or "bihar" in question_lower
            or "uttarakhand" in question_lower
            or "optical network" in question_lower
            or "power & environment" in question_lower
            or "access equipment" in question_lower
            or "field engineer" in question_lower
            or "hire" in question_lower
            or "replace" in question_lower
        ):
            metric_names = ["sla_breach_rate"]

        elif "resolution" in question_lower:
            metric_names = ["avg_resolution_time"]

        elif "dispatch" in question_lower:
            metric_names = ["dispatch_cost"]

        elif (
            "customer" in question_lower
            and "impact" in question_lower
        ):
            metric_names = ["customers_impacted"]

        elif (
            "cost per incident" in question_lower
        ):
            metric_names = ["cost_per_incident"]

        elif (
            "cost-to-serve" in question_lower
            or "cost to serve" in question_lower
            or "total cost" in question_lower
        ):
            metric_names = ["total_cost"]

        else:
            return "Sorry, I couldn't determine which KPI(s) you are asking about."

    # ----------------------------
    # Fetch verified findings
    # ----------------------------

    results = tools.get_metrics(metric_names)

    facts = "\n\n".join(
        (
            f"""Metric: {r['data']['metric']}
Value: {r['data']['display_value']}
Status: {r['data']['finding']['status']}
Business Meaning: {r['data']['finding']['business_meaning']}
Interpretation: {r['data']['finding']['interpretation']}
Headline: {r['data']['finding'].get('headline', 'None')}
Diagnostics: {r['data']['finding'].get('diagnostics', {})}
"""
        )
        for r in results
        if r["success"]
    )

    config = tools.get_config()

    period = reporting_period(
        view=config["database"]["view"],
        date_column=config["dataset"]["date_column"],
    )

    response = _client.messages.create(
        model=_model,
        system=_system_prompt,
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": f"""User Question:
{question}

Project: {config["project"]["name"]}
Reporting Period: {period["start_date"]} to {period["end_date"]}

Answer ONLY the user's question.

Keep the answer under 150 words.

For single-metric questions:

Return plain text only.

Do NOT generate:
- report headers
- project metadata
- markdown headings
- section titles
- executive report structure

Respond using exactly two short paragraphs.

Paragraph 1:
Answer the user's question directly using the verified metric.

Paragraph 2:
Include one brief evidence-based explanatory sentence only if supplied by the deterministic findings.

Use ONLY the verified findings below.

Preserve all monetary values exactly as supplied, including the ₹ symbol.

Verified Findings:

{facts}
""",
            }
        ],
    )

    return "".join(
        block.text
        for block in response.content
        if block.type == "text"
    )
"""
Deterministic business diagnostics.

Returns the highest contributing dimension values for a KPI.

No business interpretation.
No narration.
No AI.
"""

from sqlalchemy import text

from engine.db import get_engine

def top_contributor(
    view: str,
    dimension: str,
    measure: str,
    aggregation: str = "SUM",
    limit: int = 3,
    descending: bool = True,
) -> list[dict]:
    """
    Return the top contributing dimension values for a measure.
    """

    sql = text(f"""
        SELECT
            {dimension} AS category,
            {aggregation}({measure}) AS value
        FROM {view}
        GROUP BY {dimension}
        ORDER BY value {"DESC" if descending else "ASC"}
        LIMIT :limit
    """)

    with get_engine().connect() as connection:

        rows = connection.execute(
            sql,
            {"limit": limit},
        ).mappings().all()

    results = []

    for row in rows:

        value = float(row["value"])

        if aggregation == "AVG":
            display = f"{value:.2%}"
        else:
            display = (
                f"-₹{abs(value):,.2f}"
                if value < 0
                else f"₹{value:,.2f}"
  )

        results.append(
            {
                "category": row["category"],
                "value": value,
                "display": display,
            }
        )

    return results

def multi_diagnostics(
    view: str,
) -> dict:

    return {
    "top_state": top_contributor(
        view=view,
        dimension="State_UT",
        measure="SLA_Breach_Flag",
        aggregation="AVG",
    ),

    "top_vendor": top_contributor(
        view=view,
        dimension="Vendor",
        measure="SLA_Breach_Flag",
        aggregation="AVG",
    ),

    "top_fault": top_contributor(
        view=view,
        dimension="Fault_Category",
        measure="SLA_Breach_Flag",
        aggregation="AVG",
    ),
}

def retail_diagnostics(
    view: str,
) -> dict:

    return {
        "top_sales_market": top_contributor(
            view=view,
            dimension="market",
            measure="sales",
            aggregation="SUM",
        ),

        "top_profit_category": top_contributor(
            view=view,
            dimension="category",
            measure="profit",
            aggregation="SUM",
        ),

        "bottom_profit_subcategory": top_contributor(
            view=view,
            dimension="sub_category",
            measure="profit",
            aggregation="SUM",
            descending=False,
       ),

        "top_shipping_cost_ship_mode": top_contributor(
            view=view,
            dimension="ship_mode",
            measure="shipping_cost",
            aggregation="SUM",
        ),
    }

def reporting_period(
    view: str,
    date_column: str,
) -> dict:

    sql = text(f"""
        SELECT
            MIN({date_column}) AS start_date,
            MAX({date_column}) AS end_date
        FROM {view}
    """)

    with get_engine().connect() as connection:

        row = connection.execute(sql).mappings().one()

    return {
        "start_date": str(row["start_date"]),
        "end_date": str(row["end_date"]),
    }
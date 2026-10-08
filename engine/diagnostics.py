"""
Deterministic business diagnostics.

Returns grouped KPI evidence with contribution, rate comparison,
ranking, and sample-size metadata.

No business interpretation.
No narration.
No AI.
"""

from sqlalchemy import text

from engine.db import get_engine, get_source


def _query_rows(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a diagnostic query and return mapping rows."""

    with get_engine().connect() as connection:
        return connection.execute(
            text(sql),
            params or {},
        ).mappings().all()


def top_contributor(
    view: str,
    dimension: str,
    measure: str,
    aggregation: str = "SUM",
    limit: int = 3,
    descending: bool = True,
    minimum_n: int = 30,
    currency: str = "₹",
) -> list[dict]:
    """
    Return grouped KPI evidence.

    SUM:
        value
        share_of_total
        rank_by_value
        n

    AVG / rate-style metrics:
        value
        excess_vs_overall_pp
        rank_by_rate
        n

    Existing category/value/display fields are preserved for
    backward compatibility.
    """

    aggregation = aggregation.upper()

    if aggregation not in {"SUM", "AVG"}:
        raise ValueError(
            "aggregation must be either 'SUM' or 'AVG'"
        )

    if limit < 1:
        raise ValueError(
            "limit must be greater than or equal to 1"
        )

    if minimum_n < 1:
        raise ValueError(
            "minimum_n must be greater than or equal to 1"
        )

    grouped_sql = f"""
        SELECT
            {dimension} AS category,
            {aggregation}({measure}) AS value,
            COUNT(*) AS n
        FROM {view}
        GROUP BY {dimension}
        HAVING COUNT(*) >= :minimum_n
        ORDER BY value {"DESC" if descending else "ASC"}
        LIMIT :limit
    """

    rows = _query_rows(
        grouped_sql,
        {
            "limit": limit,
            "minimum_n": minimum_n,
        },
    )

    if not rows:
        return []

    total_sql = f"""
        SELECT
            {aggregation}({measure}) AS overall_value
        FROM {view}
    """

    overall_row = _query_rows(total_sql)[0]
    overall_value = overall_row["overall_value"]

    if overall_value is None:
        return []

    overall_value = float(overall_value)

    total_count = int(_query_rows(f"SELECT COUNT(*) AS total_n FROM {view}")[0]["total_n"])

    ranked_sql = f"""
        SELECT
            {dimension} AS category,
            {aggregation}({measure}) AS value,
            COUNT(*) AS n
        FROM {view}
        GROUP BY {dimension}
        HAVING COUNT(*) >= :minimum_n
        ORDER BY value DESC
    """

    ranked_rows = _query_rows(
        ranked_sql,
        {
            "minimum_n": minimum_n,
        },
    )

    rank_by_category = {
        row["category"]: index
        for index, row in enumerate(ranked_rows, start=1)
    }

    results = []

    for row in rows:

        value = float(row["value"])
        n = int(row["n"])

        if aggregation == "SUM":

            if overall_value == 0:
                share_of_total = None
            else:
                share_of_total = (
                    value / overall_value
                )

            rank = rank_by_category[row["category"]]

            display = (
                f"-{currency}{abs(value):,.2f}"
                if value < 0
                else f"{currency}{value:,.2f}"
            )

            results.append(
                {
                    "category": row["category"],
                    "value": value,
                    "display": display,
                    "n": n,
                    "share_of_total": (
                        round(share_of_total, 6)
                        if share_of_total is not None
                        else None
                    ),
                    "rank_by_value": rank,
                    "minimum_n": minimum_n,
                    "minimum_n_met": n >= minimum_n,
                }
            )

        else:

            excess_vs_overall_pp = (value - overall_value) * 100
            observed_breaches = n * value
            benchmark_breaches = n * overall_value
            excess_breaches = observed_breaches - benchmark_breaches
            total_breaches = total_count * overall_value
            incident_share = n / total_count if total_count else None
            breach_share = observed_breaches / total_breaches if total_breaches else None

            rank = rank_by_category[row["category"]]

            display = f"{value:.2%}"

            results.append(
                {
                    "category": row["category"],
                    "value": value,
                    "display": display,
                    "n": n,
                    "excess_vs_overall_pp": round(
                        excess_vs_overall_pp,
                        4,
                    ),
                    "rank_by_rate": rank,
                    "overall_rate": overall_value,
                    "observed_breaches": round(observed_breaches, 2),
                    "benchmark_breaches": round(benchmark_breaches, 2),
                    "excess_breaches": round(excess_breaches, 2),
                    "incident_share": round(incident_share, 6) if incident_share is not None else None,
                    "breach_share": round(breach_share, 6) if breach_share is not None else None,
                    "minimum_n": minimum_n,
                    "minimum_n_met": n >= minimum_n,
                }
            )

    return results


def multi_diagnostics(
    view: str,
    minimum_n: int = 30,
) -> dict:

    top_fault = top_contributor(
        view=view,
        dimension="Fault_Category",
        measure="SLA_Breach_Flag",
        aggregation="AVG",
        minimum_n=minimum_n,
    )

    overall_rate = float(
        _query_rows(
            f"SELECT AVG(SLA_Breach_Flag) AS breach_rate FROM {view}"
        )[0]["breach_rate"]
    )

    excess_breach_rows = _query_rows(
        f"""
            SELECT
                Fault_Category AS category,
                COUNT(*) AS n,
                SUM(SLA_Breach_Flag) AS observed_breaches,
                SUM(SLA_Breach_Flag) - COUNT(*) * :overall_rate AS excess_breaches
            FROM {view}
            GROUP BY Fault_Category
            HAVING COUNT(*) >= :minimum_n
            ORDER BY excess_breaches DESC
            LIMIT 3
        """,
        {
            "overall_rate": overall_rate,
            "minimum_n": minimum_n,
        },
    )

    excess_vendor_rows = _query_rows(
        f"""
            SELECT
                Vendor AS category,
                COUNT(*) AS n,
                SUM(SLA_Breach_Flag) AS observed_breaches,
                SUM(SLA_Breach_Flag) - COUNT(*) * :overall_rate AS excess_breaches
            FROM {view}
            GROUP BY Vendor
            HAVING COUNT(*) >= :minimum_n
            ORDER BY excess_breaches DESC
            LIMIT 3
        """,
        {
            "overall_rate": overall_rate,
            "minimum_n": minimum_n,
        },
    )

    excess_state_rows = _query_rows(
        f"""
            SELECT
                State_UT AS category,
                COUNT(*) AS n,
                SUM(SLA_Breach_Flag) AS observed_breaches,
                SUM(SLA_Breach_Flag) - COUNT(*) * :overall_rate AS excess_breaches
            FROM {view}
            GROUP BY State_UT
            HAVING COUNT(*) >= :minimum_n
            ORDER BY excess_breaches DESC
            LIMIT 3
        """,
        {
            "overall_rate": overall_rate,
            "minimum_n": minimum_n,
        },
    )

    cost_rows = _query_rows(
        f"""
            SELECT
                Fault_Category AS category,
                SUM(Estimated_Total_Incident_Cost) AS total_cost
            FROM {view}
            GROUP BY Fault_Category
            ORDER BY total_cost DESC
            LIMIT 3
        """
    )

    total_cost = float(
        _query_rows(
            f"SELECT SUM(Estimated_Total_Incident_Cost) AS total_cost FROM {view}"
        )[0]["total_cost"]
    )

    for row in top_fault:
        matching = next(
            (
                cost_row
                for cost_row in cost_rows
                if cost_row["category"] == row["category"]
            ),
            None,
        )

        if matching and total_cost:
            row["cost"] = round(float(matching["total_cost"]), 2)
            row["cost_share"] = round(
                float(matching["total_cost"]) / total_cost,
                6,
            )
            row["breach_concentration"] = round(
                row["breach_share"] / row["incident_share"],
                2,
            ) if row["incident_share"] else None
            row["cost_concentration"] = round(
                row["cost_share"] / row["incident_share"],
                2,
            ) if row["incident_share"] else None

    for row in top_fault:
        matching = next(
            (
                excess_row
                for excess_row in excess_breach_rows
                if excess_row["category"] == row["category"]
            ),
            None,
        )

        if matching:
            row["observed_breaches"] = int(matching["observed_breaches"])
            row["excess_breaches"] = round(
                float(matching["excess_breaches"]),
                2,
            )        

    return {
        "top_state": top_contributor(
            view=view,
            dimension="State_UT",
            measure="SLA_Breach_Flag",
            aggregation="AVG",
            minimum_n=minimum_n,
        ),
        "top_vendor": top_contributor(
            view=view,
            dimension="Vendor",
            measure="SLA_Breach_Flag",
            aggregation="AVG",
            minimum_n=minimum_n,
        ),
        "top_fault": top_fault,
        "excess_breach_fault": excess_breach_rows,
        "excess_breach_vendor": excess_vendor_rows,
        "excess_breach_state": excess_state_rows,
    }

def profit_at_risk_concentration(
    view: str,
    minimum_n: int = 30,
    currency: str = "$",
) -> list[dict]:
    """
    Identify markets disproportionately exposed to 30%+ discount losses.

    Concentration = market share of 30%+ discount losses
                    / market share of total sales.
    """

    sql = f"""
        WITH market_sales AS (
            SELECT
                market,
                SUM(sales) AS total_sales,
                COUNT(*) AS n
            FROM {view}
            GROUP BY market
            HAVING COUNT(*) >= :minimum_n
        ),
        high_discount AS (
            SELECT
                market,
                SUM(profit) AS high_discount_profit
            FROM {view}
            WHERE discount >= 0.30
            GROUP BY market
        ),
        totals AS (
            SELECT
                SUM(sales) AS total_sales,
                -SUM(
                    CASE
                        WHEN discount >= 0.30 THEN profit
                        ELSE 0
                    END
                ) AS total_loss
            FROM {view}
        )
        SELECT
            ms.market,
            ms.total_sales,
            ms.n,
            COALESCE(hd.high_discount_profit, 0) AS high_discount_profit,
            ms.total_sales / NULLIF(t.total_sales, 0) AS sales_share,
            CASE
                WHEN t.total_loss = 0 THEN 0
                ELSE -COALESCE(hd.high_discount_profit, 0) / t.total_loss
            END AS loss_share,
            CASE
                WHEN ms.total_sales = 0 OR t.total_loss = 0 THEN NULL
                ELSE (
                    -COALESCE(hd.high_discount_profit, 0) / t.total_loss
                ) / (
                    ms.total_sales / t.total_sales
                )
            END AS concentration
        FROM market_sales ms
        LEFT JOIN high_discount hd
            ON hd.market = ms.market
        CROSS JOIN totals t
        ORDER BY concentration DESC
    """

    rows = _query_rows(
        sql,
        {"minimum_n": minimum_n},
    )

    results = []

    for row in rows:
        high_discount_profit = float(row["high_discount_profit"])
        sales_share = float(row["sales_share"])
        loss_share = float(row["loss_share"])

        results.append(
            {
                "market": row["market"],
                "n": int(row["n"]),
                "total_sales": round(float(row["total_sales"]), 2),
                "high_discount_profit": round(high_discount_profit, 2),
                "high_discount_loss": round(abs(high_discount_profit), 2),
                "sales_share": round(sales_share, 6),
                "sales_share_pct": round(sales_share * 100, 2),
                "loss_share": round(loss_share, 6),
                "loss_share_pct": round(loss_share * 100, 2),
                "concentration_x": (
                    round(float(row["concentration"]), 2)
                    if row["concentration"] is not None
                    else None
                ),
                "minimum_n": minimum_n,
                "minimum_n_met": int(row["n"]) >= minimum_n,
                "currency": currency,
            }
        )

    return results

def retail_diagnostics(
    view: str,
    minimum_n: int = 30,
    currency: str = "$",
) -> dict:

    return {
        "top_sales_market": top_contributor(
            view=view,
            dimension="market",
            measure="sales",
            aggregation="SUM",
            minimum_n=minimum_n,
            currency=currency,
        ),
        "top_profit_category": top_contributor(
            view=view,
            dimension="category",
            measure="profit",
            aggregation="SUM",
            minimum_n=minimum_n,
            currency=currency,
        ),
        "bottom_profit_subcategory": top_contributor(
            view=view,
            dimension="sub_category",
            measure="profit",
            aggregation="SUM",
            descending=False,
            minimum_n=minimum_n,
            currency=currency,
        ),
        "top_shipping_cost_ship_mode": top_contributor(
            view=view,
            dimension="ship_mode",
            measure="shipping_cost",
            aggregation="SUM",
            minimum_n=minimum_n,
            currency=currency,
        ),
                "profit_at_risk_concentration": profit_at_risk_concentration(
            view=view,
            minimum_n=minimum_n,
            currency=currency,
        ),
    }


def reporting_period(
    config: dict,
) -> dict:

    source = get_source(config)
    date_column = config["dataset"]["date_column"]

    sql = f"""
        SELECT
            MIN({date_column}) AS start_date,
            MAX({date_column}) AS end_date
        FROM {source}
    """

    rows = _query_rows(sql)

    row = rows[0]

    return {
        "start_date": str(row["start_date"]),
        "end_date": str(row["end_date"]),
    }

"""
Executive KPI Scorecard Generator.
"""


def generate_scorecard(
    results: list[dict],
    config: dict,
) -> str:

    lines = [
        "## Executive KPI Scorecard",
        "",
        "| KPI | Value | Status |",
        "|---|---:|---|",
    ]

    for result in results:

        if not result["success"]:
            continue

        metric = result["data"]["metric"]
        value = result["data"]["display_value"]
        status = result["data"]["finding"]["status"]

        label = config["kpis"][metric]["label"]

        lines.append(
            f"| {label} | {value} | {status} |"
        )

    return "\n".join(lines)
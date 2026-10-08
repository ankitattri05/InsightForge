
from datetime import timedelta
from math import erf, sqrt

from dotenv import load_dotenv
from sqlalchemy import text

from engine.db import get_engine
from engine.config_loader import load_config


def aggregate(daily, start):
    breaches = 0
    total = 0

    for i in range(7):
        date = start + timedelta(days=i)
        b, n = daily[date]
        breaches += b
        total += n

    return breaches, total


def p_value(b1, n1, b0, n0):
    pooled = (b1 + b0) / (n1 + n0)
    se = sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n0))

    if se == 0:
        return 1.0

    z = abs((b1 / n1 - b0 / n0) / se)
    return 1 - erf(z / sqrt(2))


def main():
    load_dotenv()

    config = load_config("config/telecom.yaml")
    rules = config.get("materiality", {})
    min_n = rules.get("minimum_n", 30)
    min_pp = rules.get("minimum_rate_change_pp", 1.0)

    with get_engine().connect() as conn:
        rows = conn.execute(text("""
            SELECT Date, SUM(SLA_Breach_Flag), COUNT(*)
            FROM vw_incident_flat
            GROUP BY Date
            ORDER BY Date
        """)).all()

    daily = {
        row[0]: (int(row[1] or 0), int(row[2] or 0))
        for row in rows
    }

    dates = sorted(daily)
    earliest = dates[0]
    latest = dates[-1]

    comparisons = 0
    legacy_flags = 0
    significant_flags = 0
    nonsig_flags = 0

    current_end = latest

    print(f"Dataset dates: {earliest} to {latest}")
    print()
    print("FLAGGED COMPARISONS")
    print("-" * 105)

    while current_end - timedelta(days=13) >= earliest:
        current_start = current_end - timedelta(days=6)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)

        b1, n1 = aggregate(daily, current_start)
        b0, n0 = aggregate(daily, previous_start)

        comparisons += 1

        previous_rate = b0 / n0
        current_rate = b1 / n1
        pp = abs((current_rate - previous_rate) * 100)

        legacy = (
            n1 >= min_n
            and n0 >= min_n
            and pp >= min_pp
        )

        p = p_value(b1, n1, b0, n0)
        significant = p < 0.05

        if legacy:
            legacy_flags += 1

            print(
                f"Previous: {previous_start} to {previous_end}"
                f" | Current: {current_start} to {current_end}"
                f" | Previous rate: {previous_rate * 100:.2f}%"
                f" | Current rate: {current_rate * 100:.2f}%"
                f" | Change: {pp:.2f} pp"
                f" | p-value: {p:.4f}"
                f" | Significant: {'Yes' if significant else 'No'}"
            )

            if significant:
                significant_flags += 1
            else:
                nonsig_flags += 1

        current_end = previous_start - timedelta(days=1)

    print()
    print("BACKTEST SUMMARY")
    print("-" * 40)
    print(f"Dataset dates: {earliest} to {latest}")
    print(f"Adjacent 7-day comparisons: {comparisons}")
    print(f"Legacy materiality flags: {legacy_flags}")
    print(f"Statistically significant flags: {significant_flags}")
    print(f"Non-significant flags: {nonsig_flags}")

    if legacy_flags:
        share = nonsig_flags / legacy_flags * 100
        print(f"Non-significant share: {share:.1f}%")


if __name__ == "__main__":
    main()

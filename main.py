"""
InsightForge

Application entry point.

Workflow
--------
1. Load environment variables
2. Initialize analytics tools
3. Initialize narrator
4. Generate executive business brief
"""

from time import perf_counter
import os

from dotenv import load_dotenv

from agent import narrator, tools
from engine.diagnostics import reporting_period


EXPECTED_METRICS = {}


def main() -> None:

    start = perf_counter()

    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL")

    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found in .env")

    if not model:
        raise RuntimeError("ANTHROPIC_MODEL not found in .env")

    # ----------------------------
    # Initialize
    # ----------------------------

    tools.initialize(
        "config/retail.yaml",
        EXPECTED_METRICS,
    )

    narrator.initialize(
        api_key=api_key,
        model_name=model,
    )


    config = tools.get_config()

    period = reporting_period(
        view=config["database"]["view"],
        date_column=config["dataset"]["date_column"],
    )

    # ----------------------------
    # Executive Brief
    # ----------------------------

    brief = narrator.generate_brief(
        list(config["kpis"].keys())
    )

    print("=" * 80)
    print("InsightForge Executive Business Brief")
    print(config["project"]["name"])
    print(
        f"Reporting Period: {period['start_date']} to {period['end_date']}"
    )
    print("=" * 80)
    print()

    print(brief)

    # ----------------------------
    # Interactive Analyst
    # ----------------------------

    print()
    print("=" * 80)
    print("InsightForge Interactive Analyst")
    print("Type 'exit' to quit.")
    print()
    print("Example questions:")
    print("- What is the profit margin?")
    print("- Which market generated the highest sales?")
    print("- Which category generated the highest profit?")
    print("- Which ship mode incurred the highest shipping cost?")
    print("- Summarize the business performance.")
    print("=" * 80)

    try:

        while True:

            question = input("\nInsightForge > ")

            if not question.strip():
                print("Please enter a business question.")
                continue

            if question.lower() in {"exit", "quit"}:
                print("\nThank you for using InsightForge.")
                break

            print()

            try:
                answer = narrator.answer(question)
                print(answer)

            except Exception as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\n\nThank you for using InsightForge.")

    elapsed = perf_counter() - start

    print()
    print("-" * 80)
    print(f"Execution completed in {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
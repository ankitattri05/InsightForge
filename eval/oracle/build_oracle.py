import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "eval" / "oracle" / "ground_truth.json"


def load_sql(path):
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"--[^\n]*", "", content)
    return [
        statement.strip()
        for statement in content.split(";")
        if statement.strip()
    ]


def execute_statements(connection, path, question_ids):
    statements = load_sql(path)

    if len(statements) != len(question_ids):
        raise ValueError(
            f"Expected {len(question_ids)} SQL statements in {path}, "
            f"found {len(statements)}"
        )

    results = {}

    for question_id, sql in zip(question_ids, statements):
        row = connection.execute(text(sql)).mappings().first()
        results[question_id] = dict(row) if row is not None else None

    return results


def main():
    load_dotenv(ROOT / ".env")

    database_url = os.environ["DATABASE_URL"]
    engine = create_engine(database_url)

    ground_truth = {
        "version": "1.0",
        "source": "independent_sql_oracle",
        "questions": {},
    }

    telecom_path = (
        ROOT / "eval" / "oracle" / "sql" / "telecom" / "benchmark.sql"
    )

    retail_path = (
        ROOT / "eval" / "oracle" / "sql" / "retail" / "benchmark.sql"
    )

    with engine.connect() as connection:
        ground_truth["questions"].update(
            execute_statements(
                connection,
                telecom_path,
                [
                    "T01",
                    "T02",
                    "T03",
                    "T04",
                    "T05",
                    "T06",
                    "T07",
                    "T08",
                    "T09",
                ],
            )
        )

        ground_truth["questions"].update(
            execute_statements(
                connection,
                retail_path,
                [
                    "R01",
                    "R02",
                    "R03",
                    "R04",
                    "R05",
                    "R06",
                    "R07",
                    "R08",
                ],
            )
        )

    ground_truth["questions"]["T10"] = {
        "test_type": "causal_boundary"
    }

    ground_truth["questions"]["R09"] = {
        "test_type": "causal_boundary"
    }

    ground_truth["questions"]["R10"] = {
        "test_type": "causal_boundary"
    }

    OUTPUT.write_text(
        json.dumps(
            ground_truth,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(
        f"Oracle questions: "
        f"{len(ground_truth['questions'])}"
    )


if __name__ == "__main__":
    main()
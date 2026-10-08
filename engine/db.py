"""
Owns the database connection.

Nothing else in InsightForge creates a database engine directly.
"""

import os
import re

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine: Engine | None = None

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_engine() -> Engine:
    """
    Return a shared SQLAlchemy engine.

    The engine is created once and reused for the lifetime
    of the application.
    """
    global _engine

    if _engine is None:
        database_url = os.environ["DATABASE_URL"]
        _engine = create_engine(database_url)

    return _engine


def get_source(config: dict) -> str:
    """
    Return a safely qualified database source.

    MySQL uses database.view.
    SQLite tests use the local view/table name directly.
    """

    database = config["database"]["name"]
    view = config["database"]["view"]

    if not _IDENTIFIER_PATTERN.fullmatch(database):
        raise ValueError(
            f"Invalid database identifier: {database!r}"
        )

    if not _IDENTIFIER_PATTERN.fullmatch(view):
        raise ValueError(
            f"Invalid view identifier: {view!r}"
        )

    engine = get_engine()

    if engine.dialect.name == "sqlite":
        return view

    return f"{database}.{view}"


def reset_engine() -> None:
    """
    Reset the cached engine.

    Used only by unit tests to isolate test cases.
    """
    global _engine
    _engine = None
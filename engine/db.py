"""
Owns the database connection.

Nothing else in InsightForge creates a database engine directly.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine: Engine | None = None


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
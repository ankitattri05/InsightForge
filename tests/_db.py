
import os

from engine.db import get_engine


def test_get_engine_returns_engine():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    engine = get_engine()

    assert engine is not None
import os

import pytest
from sqlalchemy import text

from engine.config_loader import load_config
from engine.db import get_engine, reset_engine
from engine.metrics import calculate_metric


@pytest.fixture
def retail_config():
    return load_config("config/retail.yaml")


@pytest.fixture
def retail_sqlite_engine():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    reset_engine()
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE vw_sales_flat (
                order_id TEXT,
                sales REAL
            )
        """))

        conn.execute(text("""
            INSERT INTO vw_sales_flat
            VALUES
                ('O001', 100.0),
                ('O001', 200.0),
                ('O002', 300.0),
                ('O003', 400.0)
        """))

    return engine


def test_retail_orders_are_distinct(
    retail_config,
    retail_sqlite_engine,
):
    assert calculate_metric(
        "orders",
        retail_config,
    ) == 3.0


def test_retail_average_order_value_uses_distinct_orders(
    retail_config,
    retail_sqlite_engine,
):
    assert calculate_metric(
        "average_order_value",
        retail_config,
    ) == pytest.approx(1000.0 / 3.0)
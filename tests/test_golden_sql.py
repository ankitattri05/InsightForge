import pytest
from sqlalchemy import text

from engine.config_loader import load_config
from engine.db import get_engine, reset_engine
from engine.metrics import calculate_metric


def independent_scalar(sql: str):
    with get_engine().connect() as connection:
        return connection.execute(text(sql)).scalar()


@pytest.fixture
def real_database():
    """
    Use the real configured database for independent golden checks.

    These tests intentionally do not use the KPI SQL templates from
    engine.metrics.
    """
    from dotenv import load_dotenv

    load_dotenv()

    reset_engine()

    return get_engine()


def test_retail_orders_against_independent_sql(real_database):
    config = load_config("config/retail.yaml")

    expected = independent_scalar(
        """
        SELECT COUNT(DISTINCT order_id)
        FROM p1.vw_sales_flat
        """
    )

    actual = calculate_metric(
        "orders",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_retail_sales_against_independent_sql(real_database):
    config = load_config("config/retail.yaml")

    expected = independent_scalar(
        """
        SELECT SUM(sales)
        FROM p1.vw_sales_flat
        """
    )

    actual = calculate_metric(
        "sales",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_retail_aov_against_independent_sql(real_database):
    config = load_config("config/retail.yaml")

    expected = independent_scalar(
        """
        SELECT
            SUM(sales) /
            NULLIF(COUNT(DISTINCT order_id), 0)
        FROM p1.vw_sales_flat
        """
    )

    actual = calculate_metric(
        "average_order_value",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_telecom_incident_count_against_independent_sql(
    real_database,
):
    config = load_config("config/telecom.yaml")

    expected = independent_scalar(
        """
        SELECT COUNT(*)
        FROM telecom_service_assurance.vw_incident_flat
        """
    )

    actual = calculate_metric(
        "incident_count",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_telecom_sla_breach_rate_against_independent_sql(
    real_database,
):
    config = load_config("config/telecom.yaml")

    expected = independent_scalar(
        """
        SELECT AVG(SLA_Breach_Flag)
        FROM telecom_service_assurance.vw_incident_flat
        """
    )

    actual = calculate_metric(
        "sla_breach_rate",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_telecom_resolution_time_against_independent_sql(
    real_database,
):
    config = load_config("config/telecom.yaml")

    expected = independent_scalar(
        """
        SELECT AVG(Resolution_Minutes)
        FROM telecom_service_assurance.vw_incident_flat
        """
    )

    actual = calculate_metric(
        "avg_resolution_time",
        config,
    )

    assert actual == pytest.approx(float(expected))


def test_telecom_total_cost_against_independent_sql(
    real_database,
):
    config = load_config("config/telecom.yaml")

    expected = independent_scalar(
        """
        SELECT SUM(Estimated_Total_Incident_Cost)
        FROM telecom_service_assurance.vw_incident_flat
        """
    )

    actual = calculate_metric(
        "total_cost",
        config,
    )

    assert actual == pytest.approx(float(expected))
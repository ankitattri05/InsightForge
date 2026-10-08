import pytest
from dotenv import load_dotenv
from sqlalchemy import text

from engine.db import get_engine, reset_engine


@pytest.fixture
def real_database():
    """
    Run business-invariant checks against the real configured database.

    These checks validate relationships in the analytical dataset itself,
    rather than testing individual application functions.
    """
    load_dotenv()
    reset_engine()
    return get_engine()


def test_fact_and_view_row_counts_reconcile(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT
                (SELECT COUNT(*)
                 FROM telecom_service_assurance.fact_incident) AS fact_rows,
                (SELECT COUNT(*)
                 FROM telecom_service_assurance.vw_incident_flat) AS view_rows
            """
        )
    ).fetchone()

    assert result.fact_rows == result.view_rows == 25000


def test_view_has_unique_incidents(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT
                COUNT(*) AS view_rows,
                COUNT(DISTINCT Incident_ID) AS distinct_incidents
            FROM telecom_service_assurance.vw_incident_flat
            """
        )
    ).fetchone()

    assert result.view_rows == result.distinct_incidents == 25000


def test_sla_breach_count_reconciles(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT
                SUM(SLA_Breach = 'Yes') AS stored_breaches,
                SUM(Resolution_Minutes > SLA_Target_Minutes)
                    AS calculated_breaches
            FROM telecom_service_assurance.fact_incident
            """
        )
    ).fetchone()

    assert result.stored_breaches == result.calculated_breaches == 2497


def test_sla_business_rule_has_no_mismatches(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT COUNT(*) AS mismatches
            FROM telecom_service_assurance.fact_incident
            WHERE
                (SLA_Breach = 'Yes'
                 AND Resolution_Minutes <= SLA_Target_Minutes)
                OR
                (SLA_Breach = 'No'
                 AND Resolution_Minutes > SLA_Target_Minutes)
            """
        )
    ).scalar()

    assert result == 0


def test_total_cost_reconciles_to_cost_components(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT COUNT(*) AS mismatches
            FROM telecom_service_assurance.fact_incident
            WHERE ABS(
                Estimated_Total_Incident_Cost
                - (
                    Estimated_Operational_Cost
                    + Estimated_Service_Impact_Cost
                )
            ) > 0.01
            """
        )
    ).scalar()

    assert result == 0


def test_non_dispatch_incidents_have_zero_dispatch_cost(real_database):
    result = real_database.connect().execute(
        text(
            """
            SELECT COUNT(*) AS violations
            FROM telecom_service_assurance.fact_incident
            WHERE Dispatch_Required = 'No'
              AND Dispatch_Cost <> 0
            """
        )
    ).scalar()

    assert result == 0
-- InsightForge Independent Evaluation Oracle - Telecom T01-T10
-- T01
SELECT AVG(SLA_Breach_Flag) AS expected_value FROM telecom_service_assurance.vw_incident_flat;
-- T02
SELECT AVG(Resolution_Minutes) AS expected_value FROM telecom_service_assurance.vw_incident_flat;
-- T03
SELECT SUM(Estimated_Total_Incident_Cost) AS expected_value FROM telecom_service_assurance.vw_incident_flat;
-- T04
SELECT SUM(Dispatch_Cost) AS expected_value FROM telecom_service_assurance.vw_incident_flat;
-- T05
SELECT SUM(Customers_Impacted) AS expected_value FROM telecom_service_assurance.vw_incident_flat;
-- T06
SELECT State_UT AS expected_entity, AVG(SLA_Breach_Flag) AS expected_value, COUNT(*) AS n FROM telecom_service_assurance.vw_incident_flat GROUP BY State_UT HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- T07
SELECT Vendor AS expected_entity, AVG(SLA_Breach_Flag) AS expected_value, COUNT(*) AS n FROM telecom_service_assurance.vw_incident_flat GROUP BY Vendor HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- T08
SELECT Fault_Category AS expected_entity, AVG(SLA_Breach_Flag) AS expected_value, COUNT(*) AS n FROM telecom_service_assurance.vw_incident_flat GROUP BY Fault_Category HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- T09
WITH latest AS (SELECT MAX(Date) AS latest_date FROM telecom_service_assurance.vw_incident_flat), rates AS (SELECT AVG(CASE WHEN Date BETWEEN DATE_SUB(latest_date, INTERVAL 6 DAY) AND latest_date THEN SLA_Breach_Flag END) AS current_rate, AVG(CASE WHEN Date BETWEEN DATE_SUB(latest_date, INTERVAL 13 DAY) AND DATE_SUB(latest_date, INTERVAL 7 DAY) THEN SLA_Breach_Flag END) AS previous_rate FROM telecom_service_assurance.vw_incident_flat CROSS JOIN latest) SELECT current_rate, previous_rate, (current_rate-previous_rate)*100 AS percentage_point_change, ((current_rate-previous_rate)/NULLIF(previous_rate,0))*100 AS relative_change_pct, CASE WHEN ABS(((current_rate-previous_rate)/NULLIF(previous_rate,0))*100)<1 THEN 'Stable' WHEN current_rate>previous_rate THEN 'Increase' ELSE 'Decrease' END AS direction FROM rates;
-- T10 is a causal-boundary test; no numeric oracle.

USE telecom_service_assurance;

DROP VIEW IF EXISTS vw_incident_flat;

CREATE VIEW vw_incident_flat AS
SELECT
    -- Date
    d.Date_ID,
    d.Date,
    d.Year,
    d.Quarter,
    d.Month_Number,
    d.Month_Name,
    d.Month_Short,
    d.Year_Month,

    -- Site
    s.Site_ID,
    s.Zone,
    s.State_UT,
    s.Circle,
    s.City,
    s.Site_Cluster,
    s.Site_Type,

    -- Vendor
    vt.VendorTech_ID,
    vt.Vendor,
    vt.Technology,

    -- Incident
    f.Incident_ID,
    f.Fault_ID,
    f.Fault_Name,
    f.Fault_Category,
    f.Network_Layer,
    f.Fault_Type,

    f.Severity,
    f.Resolution_Type,
    f.Resolution_Minutes,
    f.SLA_Target_Minutes,

    CASE
        WHEN f.SLA_Breach = 'Yes' THEN 1
        ELSE 0
    END AS SLA_Breach_Flag,

    f.Customers_Impacted,
    f.Dispatch_Required,
    f.Dispatch_Cost,

    f.Estimated_Operational_Cost,
    f.Estimated_Service_Impact_Cost,
    f.Estimated_Total_Incident_Cost,

    f.Repeat_Fault,
    f.Escalation

FROM fact_incident f
INNER JOIN dim_date d
    ON f.Date_ID = d.Date_ID
INNER JOIN dim_site s
    ON f.Site_ID = s.Site_ID
INNER JOIN dim_vendortechnology vt
    ON f.VendorTech_ID = vt.VendorTech_ID;
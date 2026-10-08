-- InsightForge Independent Evaluation Oracle - Retail R01-R10
-- R01
SELECT SUM(sales) AS expected_value FROM p1.vw_sales_flat;
-- R02
SELECT SUM(profit) AS expected_value FROM p1.vw_sales_flat;
-- R03
SELECT SUM(profit) / NULLIF(SUM(sales),0) AS expected_value FROM p1.vw_sales_flat;
-- R04
SELECT SUM(sales) / NULLIF(COUNT(DISTINCT order_id),0) AS expected_value FROM p1.vw_sales_flat;
-- R05
SELECT market AS expected_entity, SUM(sales) AS expected_value, COUNT(*) AS n FROM p1.vw_sales_flat GROUP BY market HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- R06
SELECT category AS expected_entity, SUM(profit) AS expected_value, COUNT(*) AS n FROM p1.vw_sales_flat GROUP BY category HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- R07
SELECT sub_category AS expected_entity, SUM(profit) AS expected_value, COUNT(*) AS n FROM p1.vw_sales_flat GROUP BY sub_category HAVING COUNT(*) >= 30 ORDER BY expected_value ASC LIMIT 1;
-- R08
SELECT ship_mode AS expected_entity, SUM(shipping_cost) AS expected_value, COUNT(*) AS n FROM p1.vw_sales_flat GROUP BY ship_mode HAVING COUNT(*) >= 30 ORDER BY expected_value DESC LIMIT 1;
-- R09 is a causal-boundary test; no numeric oracle.
-- R10 is a causal-boundary test; no numeric oracle.

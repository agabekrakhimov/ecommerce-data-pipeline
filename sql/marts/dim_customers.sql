-- Dimension: one row per customer. cohort_month anchors retention analysis.
DROP TABLE IF EXISTS dim_customers;

CREATE TABLE dim_customers AS
SELECT
    customer_id,
    customer_name,
    country,
    segment,
    signup_date,
    signup_month        AS cohort_month
FROM stg_customers;

CREATE UNIQUE INDEX idx_dim_customers_pk ON dim_customers (customer_id);

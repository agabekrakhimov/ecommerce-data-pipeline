-- Staging: typecast + light cleaning of raw_customers.
DROP VIEW IF EXISTS stg_customers;

CREATE VIEW stg_customers AS
SELECT
    CAST(customer_id AS INTEGER)        AS customer_id,
    TRIM(name)                          AS customer_name,
    DATE(signup_date)                   AS signup_date,
    SUBSTR(signup_date, 1, 7)           AS signup_month,   -- YYYY-MM
    TRIM(country)                       AS country,
    TRIM(segment)                       AS segment
FROM raw_customers
WHERE customer_id IS NOT NULL;

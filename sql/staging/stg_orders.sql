-- Staging: typecast + light cleaning of raw_orders.
DROP VIEW IF EXISTS stg_orders;

CREATE VIEW stg_orders AS
SELECT
    CAST(order_id AS INTEGER)           AS order_id,
    CAST(customer_id AS INTEGER)        AS customer_id,
    DATE(order_date)                    AS order_date,
    SUBSTR(order_date, 1, 7)            AS order_month,     -- YYYY-MM
    LOWER(TRIM(status))                 AS status
FROM raw_orders
WHERE order_id IS NOT NULL;

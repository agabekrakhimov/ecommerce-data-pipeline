-- Staging: typecast + light cleaning of raw_products.
DROP VIEW IF EXISTS stg_products;

CREATE VIEW stg_products AS
SELECT
    CAST(product_id AS INTEGER)         AS product_id,
    TRIM(product_name)                  AS product_name,
    TRIM(category)                      AS category,
    CAST(price AS REAL)                 AS price,
    CAST(cost AS REAL)                  AS cost
FROM raw_products
WHERE product_id IS NOT NULL;

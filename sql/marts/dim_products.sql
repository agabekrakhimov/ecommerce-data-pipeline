-- Dimension: one row per product, with a derived unit margin.
DROP TABLE IF EXISTS dim_products;

CREATE TABLE dim_products AS
SELECT
    product_id,
    product_name,
    category,
    price,
    cost,
    ROUND(price - cost, 2)                                  AS unit_margin,
    CASE WHEN price > 0
         THEN ROUND((price - cost) / price, 4)
         ELSE 0 END                                         AS margin_pct
FROM stg_products;

CREATE UNIQUE INDEX idx_dim_products_pk ON dim_products (product_id);

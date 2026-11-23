-- name: marts.not_empty
-- table: marts
-- category: completeness
-- description: dim_customers, dim_products, and fct_orders each have at least one row

SELECT 'dim_customers' AS table_name
WHERE NOT EXISTS (SELECT 1 FROM dim_customers)

UNION ALL

SELECT 'dim_products' AS table_name
WHERE NOT EXISTS (SELECT 1 FROM dim_products)

UNION ALL

SELECT 'fct_orders' AS table_name
WHERE NOT EXISTS (SELECT 1 FROM fct_orders)

-- name: fct_orders.product_fk
-- table: fct_orders
-- category: referential
-- description: Every order line points at a product that exists in dim_products

SELECT f.order_item_id, f.product_id
FROM fct_orders f
LEFT JOIN dim_products p
    ON p.product_id = f.product_id
WHERE f.product_id IS NOT NULL
  AND p.product_id IS NULL

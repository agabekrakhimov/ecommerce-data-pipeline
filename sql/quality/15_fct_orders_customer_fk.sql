-- name: fct_orders.customer_fk
-- table: fct_orders
-- category: referential
-- description: Every order line points at a customer that exists in dim_customers

SELECT f.order_item_id, f.customer_id
FROM fct_orders f
LEFT JOIN dim_customers c
    ON c.customer_id = f.customer_id
WHERE f.customer_id IS NOT NULL
  AND c.customer_id IS NULL

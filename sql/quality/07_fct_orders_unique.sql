-- name: fct_orders.order_item_id_unique
-- table: fct_orders
-- category: duplicate
-- description: Fact grain is one row per order_item_id. Null ids are left to the null check

SELECT order_item_id, COUNT(*) AS row_count
FROM fct_orders
WHERE order_item_id IS NOT NULL
GROUP BY order_item_id
HAVING COUNT(*) > 1

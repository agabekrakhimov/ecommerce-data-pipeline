-- name: fct_orders.not_null
-- table: fct_orders
-- category: null
-- description: Every order line has a grain key, foreign keys, status, dates, and measures

SELECT order_item_id, 'order_item_id' AS column_name
FROM fct_orders
WHERE order_item_id IS NULL

UNION ALL

SELECT order_item_id, 'order_id' AS column_name
FROM fct_orders
WHERE order_id IS NULL

UNION ALL

SELECT order_item_id, 'customer_id' AS column_name
FROM fct_orders
WHERE customer_id IS NULL

UNION ALL

SELECT order_item_id, 'product_id' AS column_name
FROM fct_orders
WHERE product_id IS NULL

UNION ALL

SELECT order_item_id, 'order_date' AS column_name
FROM fct_orders
WHERE order_date IS NULL OR TRIM(order_date) = ''

UNION ALL

SELECT order_item_id, 'order_month' AS column_name
FROM fct_orders
WHERE order_month IS NULL OR TRIM(order_month) = ''

UNION ALL

SELECT order_item_id, 'status' AS column_name
FROM fct_orders
WHERE status IS NULL OR TRIM(status) = ''

UNION ALL

SELECT order_item_id, 'quantity' AS column_name
FROM fct_orders
WHERE quantity IS NULL

UNION ALL

SELECT order_item_id, 'unit_price' AS column_name
FROM fct_orders
WHERE unit_price IS NULL

UNION ALL

SELECT order_item_id, 'revenue' AS column_name
FROM fct_orders
WHERE revenue IS NULL

UNION ALL

SELECT order_item_id, 'cost_amount' AS column_name
FROM fct_orders
WHERE cost_amount IS NULL

UNION ALL

SELECT order_item_id, 'gross_profit' AS column_name
FROM fct_orders
WHERE gross_profit IS NULL

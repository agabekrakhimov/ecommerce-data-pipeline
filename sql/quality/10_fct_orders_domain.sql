-- name: fct_orders.domain
-- table: fct_orders
-- category: range
-- description: Quantity, unit price, status, and order date stay inside the mart's domain

SELECT order_item_id, 'order_item_id' AS issue
FROM fct_orders
WHERE order_item_id IS NOT NULL
  AND order_item_id <= 0

UNION ALL

SELECT order_item_id, 'quantity' AS issue
FROM fct_orders
WHERE quantity IS NOT NULL
  AND quantity < 1

UNION ALL

SELECT order_item_id, 'unit_price' AS issue
FROM fct_orders
WHERE unit_price IS NOT NULL
  AND unit_price < 0

UNION ALL

SELECT order_item_id, 'status' AS issue
FROM fct_orders
WHERE status IS NOT NULL
  AND TRIM(status) != ''
  AND status NOT IN ('completed', 'cancelled', 'returned', 'pending')

UNION ALL

-- date() rolls impossible days forward, so the stored text must equal date().
SELECT order_item_id, 'order_date' AS issue
FROM fct_orders
WHERE order_date IS NOT NULL
  AND TRIM(order_date) != ''
  AND (
      order_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
      OR date(order_date) IS NULL
      OR order_date != date(order_date)
      OR order_date < '2024-01-01'
      OR order_date > '2025-12-31'
  )

-- name: fct_orders.order_month
-- table: fct_orders
-- category: consistency
-- description: order_month is the calendar month of order_date (YYYY-MM)

SELECT order_item_id, order_date, order_month
FROM fct_orders
WHERE order_date IS NOT NULL
  AND TRIM(order_date) != ''
  AND date(order_date) IS NOT NULL
  AND (
      order_month IS NULL
      OR order_month != SUBSTR(order_date, 1, 7)
  )

-- name: fct_orders.measures
-- table: fct_orders
-- category: consistency
-- description: revenue, cost_amount, and gross_profit match quantity, unit price, and product cost

SELECT order_item_id, 'revenue' AS issue
FROM fct_orders
WHERE quantity IS NOT NULL
  AND unit_price IS NOT NULL
  AND (
      revenue IS NULL
      OR ABS(revenue - ROUND(quantity * unit_price, 2)) > 0.01
  )

UNION ALL

SELECT f.order_item_id, 'cost_amount' AS issue
FROM fct_orders f
JOIN dim_products p
    ON p.product_id = f.product_id
WHERE f.quantity IS NOT NULL
  AND p.cost IS NOT NULL
  AND (
      f.cost_amount IS NULL
      OR ABS(f.cost_amount - ROUND(f.quantity * p.cost, 2)) > 0.01
  )

UNION ALL

-- Same expression the mart uses. Comparing gross_profit to the already
-- rounded revenue and cost_amount can disagree by a cent.
SELECT f.order_item_id, 'gross_profit' AS issue
FROM fct_orders f
JOIN dim_products p
    ON p.product_id = f.product_id
WHERE f.quantity IS NOT NULL
  AND f.unit_price IS NOT NULL
  AND p.cost IS NOT NULL
  AND (
      f.gross_profit IS NULL
      OR ABS(
          f.gross_profit - ROUND(
              f.quantity * f.unit_price - f.quantity * p.cost,
              2
          )
      ) > 0.01
  )

-- name: dim_products.margins
-- table: dim_products
-- category: consistency
-- description: unit_margin and margin_pct match price and cost

SELECT product_id, 'unit_margin' AS issue
FROM dim_products
WHERE price IS NOT NULL
  AND cost IS NOT NULL
  AND (
      unit_margin IS NULL
      OR ABS(unit_margin - ROUND(price - cost, 2)) > 0.01
  )

UNION ALL

SELECT product_id, 'margin_pct' AS issue
FROM dim_products
WHERE price IS NOT NULL
  AND price > 0
  AND cost IS NOT NULL
  AND (
      margin_pct IS NULL
      OR ABS(margin_pct - ROUND((price - cost) / price, 4)) > 0.0001
  )

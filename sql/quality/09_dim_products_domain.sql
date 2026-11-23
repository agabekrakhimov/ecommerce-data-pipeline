-- name: dim_products.domain
-- table: dim_products
-- category: range
-- description: Category is known, price is positive, and cost sits between zero and price

SELECT product_id, 'product_id' AS issue
FROM dim_products
WHERE product_id IS NOT NULL
  AND product_id <= 0

UNION ALL

SELECT product_id, 'category' AS issue
FROM dim_products
WHERE category IS NOT NULL
  AND TRIM(category) != ''
  AND category NOT IN (
      'Electronics',
      'Home & Kitchen',
      'Clothing',
      'Sports & Outdoors',
      'Books',
      'Beauty',
      'Toys',
      'Grocery'
  )

UNION ALL

SELECT product_id, 'price' AS issue
FROM dim_products
WHERE price IS NOT NULL
  AND price <= 0

UNION ALL

SELECT product_id, 'cost' AS issue
FROM dim_products
WHERE cost IS NOT NULL
  AND cost < 0

UNION ALL

SELECT product_id, 'cost_above_price' AS issue
FROM dim_products
WHERE price IS NOT NULL
  AND cost IS NOT NULL
  AND cost > price

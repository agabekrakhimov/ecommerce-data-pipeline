-- name: dim_products.not_null
-- table: dim_products
-- category: null
-- description: Product attributes used by the marts are present (blank strings count as missing)

SELECT product_id, 'product_id' AS column_name
FROM dim_products
WHERE product_id IS NULL

UNION ALL

SELECT product_id, 'product_name' AS column_name
FROM dim_products
WHERE product_name IS NULL OR TRIM(product_name) = ''

UNION ALL

SELECT product_id, 'category' AS column_name
FROM dim_products
WHERE category IS NULL OR TRIM(category) = ''

UNION ALL

SELECT product_id, 'price' AS column_name
FROM dim_products
WHERE price IS NULL

UNION ALL

SELECT product_id, 'cost' AS column_name
FROM dim_products
WHERE cost IS NULL

UNION ALL

SELECT product_id, 'unit_margin' AS column_name
FROM dim_products
WHERE unit_margin IS NULL

UNION ALL

SELECT product_id, 'margin_pct' AS column_name
FROM dim_products
WHERE margin_pct IS NULL

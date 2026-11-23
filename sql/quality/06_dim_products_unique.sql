-- name: dim_products.product_id_unique
-- table: dim_products
-- category: duplicate
-- description: product_id is unique. Null ids are left to the null check (SQLite groups those together)

SELECT product_id, COUNT(*) AS row_count
FROM dim_products
WHERE product_id IS NOT NULL
GROUP BY product_id
HAVING COUNT(*) > 1

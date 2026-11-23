-- name: dim_customers.customer_id_unique
-- table: dim_customers
-- category: duplicate
-- description: customer_id is unique. Null ids are left to the null check (SQLite groups those together)

SELECT customer_id, COUNT(*) AS row_count
FROM dim_customers
WHERE customer_id IS NOT NULL
GROUP BY customer_id
HAVING COUNT(*) > 1

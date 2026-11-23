-- name: dim_customers.not_null
-- table: dim_customers
-- category: null
-- description: Customer attributes used by the marts are present (blank strings count as missing)

SELECT customer_id, 'customer_id' AS column_name
FROM dim_customers
WHERE customer_id IS NULL

UNION ALL

SELECT customer_id, 'customer_name' AS column_name
FROM dim_customers
WHERE customer_name IS NULL OR TRIM(customer_name) = ''

UNION ALL

SELECT customer_id, 'country' AS column_name
FROM dim_customers
WHERE country IS NULL OR TRIM(country) = ''

UNION ALL

SELECT customer_id, 'segment' AS column_name
FROM dim_customers
WHERE segment IS NULL OR TRIM(segment) = ''

UNION ALL

SELECT customer_id, 'signup_date' AS column_name
FROM dim_customers
WHERE signup_date IS NULL OR TRIM(signup_date) = ''

UNION ALL

SELECT customer_id, 'cohort_month' AS column_name
FROM dim_customers
WHERE cohort_month IS NULL OR TRIM(cohort_month) = ''

-- name: dim_customers.cohort_month
-- table: dim_customers
-- category: consistency
-- description: cohort_month is the signup month (YYYY-MM)

SELECT customer_id, signup_date, cohort_month
FROM dim_customers
WHERE signup_date IS NOT NULL
  AND TRIM(signup_date) != ''
  AND date(signup_date) IS NOT NULL
  AND cohort_month IS NOT NULL
  AND cohort_month != SUBSTR(signup_date, 1, 7)

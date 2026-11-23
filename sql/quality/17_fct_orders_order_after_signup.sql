-- name: fct_orders.order_after_signup
-- table: fct_orders
-- category: referential
-- description: An order is not placed in a month before the customer's signup month

SELECT
    f.order_item_id,
    f.order_month,
    c.customer_id,
    c.cohort_month
FROM fct_orders f
JOIN dim_customers c
    ON c.customer_id = f.customer_id
WHERE f.order_month IS NOT NULL
  AND c.cohort_month IS NOT NULL
  AND f.order_month < c.cohort_month

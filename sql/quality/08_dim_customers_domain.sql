-- name: dim_customers.domain
-- table: dim_customers
-- category: range
-- description: Segment, country, and signup date stay inside the values the generator produces

SELECT customer_id, 'customer_id' AS issue
FROM dim_customers
WHERE customer_id IS NOT NULL
  AND customer_id <= 0

UNION ALL

SELECT customer_id, 'segment' AS issue
FROM dim_customers
WHERE segment IS NOT NULL
  AND TRIM(segment) != ''
  AND segment NOT IN ('Consumer', 'SMB', 'Enterprise')

UNION ALL

SELECT customer_id, 'country' AS issue
FROM dim_customers
WHERE country IS NOT NULL
  AND TRIM(country) != ''
  AND country NOT IN (
      'United States',
      'United Kingdom',
      'Germany',
      'Canada',
      'France',
      'Australia',
      'India',
      'Brazil',
      'Japan'
  )

UNION ALL

-- date() rolls impossible days forward (2024-02-31 -> 2024-03-02), so the
-- stored text has to equal date(signup_date), not merely parse.
SELECT customer_id, 'signup_date' AS issue
FROM dim_customers
WHERE signup_date IS NOT NULL
  AND TRIM(signup_date) != ''
  AND (
      signup_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
      OR date(signup_date) IS NULL
      OR signup_date != date(signup_date)
      OR signup_date < '2024-01-01'
      OR signup_date > '2025-12-31'
  )

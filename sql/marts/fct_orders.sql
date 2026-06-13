-- Fact: one row per order line item (the grain of the star schema).
-- Joins orders -> order_items -> products and carries foreign keys to both
-- dimensions plus the additive measures (revenue, cost, gross profit).
DROP TABLE IF EXISTS fct_orders;

CREATE TABLE fct_orders AS
SELECT
    oi.order_item_id,
    o.order_id,
    o.customer_id,                                  -- FK -> dim_customers
    oi.product_id,                                  -- FK -> dim_products
    o.order_date,
    o.order_month,
    o.status,
    oi.quantity,
    oi.unit_price,
    ROUND(oi.quantity * oi.unit_price, 2)                       AS revenue,
    ROUND(oi.quantity * p.cost, 2)                             AS cost_amount,
    ROUND(oi.quantity * oi.unit_price - oi.quantity * p.cost, 2) AS gross_profit
FROM stg_orders o
JOIN stg_order_items oi ON oi.order_id = o.order_id
JOIN stg_products   p  ON p.product_id = oi.product_id;

CREATE INDEX idx_fct_orders_customer ON fct_orders (customer_id);
CREATE INDEX idx_fct_orders_product  ON fct_orders (product_id);
CREATE INDEX idx_fct_orders_month    ON fct_orders (order_month);

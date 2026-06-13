-- Staging: typecast + light cleaning of raw_order_items.
DROP VIEW IF EXISTS stg_order_items;

CREATE VIEW stg_order_items AS
SELECT
    CAST(order_item_id AS INTEGER)      AS order_item_id,
    CAST(order_id AS INTEGER)           AS order_id,
    CAST(product_id AS INTEGER)         AS product_id,
    CAST(quantity AS INTEGER)           AS quantity,
    CAST(unit_price AS REAL)            AS unit_price
FROM raw_order_items
WHERE order_item_id IS NOT NULL;

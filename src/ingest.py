"""Load the raw CSVs into a SQLite warehouse as raw_* tables.

SQLite (stdlib `sqlite3`) stands in for a columnar warehouse like DuckDB while
keeping the project dependency-free. The staging/marts SQL layers run on top of
these raw landing tables, mirroring an ELT (extract-load-transform) flow.
"""

import csv
import os
import sqlite3

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "warehouse.sqlite")

# Raw table -> (csv file, column definitions). Everything lands as TEXT to
# mimic an untyped landing zone; the staging layer does the typecasting.
RAW_TABLES = {
    "raw_customers": (
        "customers.csv",
        ["customer_id", "name", "signup_date", "country", "segment"],
    ),
    "raw_products": (
        "products.csv",
        ["product_id", "product_name", "category", "price", "cost"],
    ),
    "raw_orders": (
        "orders.csv",
        ["order_id", "customer_id", "order_date", "status"],
    ),
    "raw_order_items": (
        "order_items.csv",
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    ),
}


def _load_table(conn, table, csv_file, columns):
    path = os.path.join(RAW_DIR, csv_file)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Missing raw file {} - run generate_data.py first.".format(path)
        )

    cols_ddl = ", ".join("{} TEXT".format(c) for c in columns)
    conn.execute("DROP TABLE IF EXISTS {}".format(table))
    conn.execute("CREATE TABLE {} ({})".format(table, cols_ddl))

    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table, ", ".join(columns), placeholders
    )

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [tuple(row[c] for c in columns) for row in reader]

    conn.executemany(insert_sql, rows)
    return len(rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        for table, (csv_file, columns) in RAW_TABLES.items():
            count = _load_table(conn, table, csv_file, columns)
            print("  loaded {:<18} {:>7,} rows".format(table, count))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

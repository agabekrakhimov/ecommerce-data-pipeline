"""One-command orchestrator for the e-commerce analytics pipeline.

    python3 run_pipeline.py

Runs end-to-end with the Python standard library only:
  1. generate  -> synthetic raw CSVs in data/raw/
  2. ingest     -> load raw CSVs into warehouse.sqlite (raw_* tables)
  3. staging    -> clean/typecast SQL views (stg_*)
  4. marts      -> star-schema tables (dim_customers, dim_products, fct_orders)
  5. analysis   -> business-question SQL -> outputs/insights.md + SVG charts
"""

import glob
import os
import sqlite3
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
sys.path.insert(0, SRC)

import generate_data       # noqa: E402
import ingest              # noqa: E402
import analysis            # noqa: E402

DB_PATH = os.path.join(BASE, "warehouse.sqlite")


def _banner(step, title):
    print("\n[{}/5] {}".format(step, title))
    print("-" * 52)


def run_sql_dir(conn, folder):
    """Execute every .sql file in a folder, in sorted order."""
    pattern = os.path.join(BASE, "sql", folder, "*.sql")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError("No SQL files found in sql/{}/".format(folder))
    for path in files:
        with open(path) as f:
            conn.executescript(f.read())
        print("  ran {}".format(os.path.relpath(path, BASE)))
    conn.commit()


def main():
    start = time.time()
    print("=" * 52)
    print(" ecommerce-data-pipeline  |  stdlib-only ELT")
    print("=" * 52)

    _banner(1, "Generate raw data")
    generate_data.main()

    _banner(2, "Ingest raw CSVs -> warehouse.sqlite")
    ingest.main()

    conn = sqlite3.connect(DB_PATH)
    try:
        _banner(3, "Staging (clean + typecast)")
        run_sql_dir(conn, "staging")

        _banner(4, "Marts (star schema)")
        run_sql_dir(conn, "marts")
    finally:
        conn.close()

    _banner(5, "Analysis (SQL + charts + insights)")
    analysis.main()

    print("\n" + "=" * 52)
    print(" Done in {:.1f}s. See outputs/insights.md and outputs/charts/.".format(
        time.time() - start))
    print("=" * 52)


if __name__ == "__main__":
    main()

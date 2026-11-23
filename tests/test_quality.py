"""Unit tests for the mart data-quality gate.

The dirty-mart test plants nulls, duplicate keys, out-of-range values, broken
foreign keys, and measures that do not match the line math. The violation
totals asserted here are the ones quoted in the README.
"""

import sqlite3

import pytest

import quality


CUSTOMERS_OK = [
    {
        "customer_id": 1,
        "customer_name": "Alex Smith",
        "country": "United States",
        "segment": "Consumer",
        "signup_date": "2024-03-15",
        "cohort_month": "2024-03",
    },
    {
        "customer_id": 2,
        "customer_name": "Sam Muller",
        "country": "Germany",
        "segment": "SMB",
        "signup_date": "2024-01-10",
        "cohort_month": "2024-01",
    },
    {
        "customer_id": 7,
        "customer_name": "Yuki Tanaka",
        "country": "Japan",
        "segment": "Consumer",
        "signup_date": "2024-02-29",  # leap day, must stay valid
        "cohort_month": "2024-02",
    },
]

PRODUCTS_OK = [
    {
        "product_id": 1,
        "product_name": "Electronics Item 0001",
        "category": "Electronics",
        "price": 100.0,
        "cost": 68.0,
        "unit_margin": 32.0,
        "margin_pct": 0.32,
    },
    {
        "product_id": 2,
        "product_name": "Books Item 0002",
        "category": "Books",
        "price": 20.0,
        "cost": 12.0,
        "unit_margin": 8.0,
        "margin_pct": 0.4,
    },
]

FACTS_OK = [
    {
        "order_item_id": 1,
        "order_id": 1,
        "customer_id": 1,
        "product_id": 1,
        "order_date": "2024-06-01",
        "order_month": "2024-06",
        "status": "completed",
        "quantity": 2,
        "unit_price": 90.0,
        "revenue": 180.0,
        "cost_amount": 136.0,
        "gross_profit": 44.0,
    },
    {
        "order_item_id": 8,
        "order_id": 8,
        "customer_id": 7,
        "product_id": 1,
        "order_date": "2024-02-29",
        "order_month": "2024-02",
        "status": "completed",
        "quantity": 1,
        "unit_price": 100.0,
        "revenue": 100.0,
        "cost_amount": 68.0,
        "gross_profit": 32.0,
    },
]

# One row per duplicated key, so these counts are keys rather than extra rows.
EXPECTED_VIOLATIONS = {
    "marts.not_empty": 0,
    "dim_customers.not_null": 6,
    "dim_products.not_null": 6,
    "fct_orders.not_null": 12,
    "dim_customers.customer_id_unique": 1,
    "dim_products.product_id_unique": 1,
    "fct_orders.order_item_id_unique": 1,
    "dim_customers.domain": 3,
    "dim_products.domain": 4,
    "fct_orders.domain": 4,
    "dim_customers.cohort_month": 1,
    "dim_products.margins": 2,
    "fct_orders.measures": 3,
    "fct_orders.order_month": 1,
    "fct_orders.customer_fk": 1,
    "fct_orders.product_fk": 1,
    "fct_orders.order_after_signup": 1,
}


def create_marts(conn):
    conn.executescript(
        """
        CREATE TABLE dim_customers (
            customer_id INTEGER,
            customer_name TEXT,
            country TEXT,
            segment TEXT,
            signup_date TEXT,
            cohort_month TEXT
        );
        CREATE TABLE dim_products (
            product_id INTEGER,
            product_name TEXT,
            category TEXT,
            price REAL,
            cost REAL,
            unit_margin REAL,
            margin_pct REAL
        );
        CREATE TABLE fct_orders (
            order_item_id INTEGER,
            order_id INTEGER,
            customer_id INTEGER,
            product_id INTEGER,
            order_date TEXT,
            order_month TEXT,
            status TEXT,
            quantity INTEGER,
            unit_price REAL,
            revenue REAL,
            cost_amount REAL,
            gross_profit REAL
        );
        """
    )


def insert(conn, table, rows):
    cols = list(rows[0].keys())
    sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table, ", ".join(cols), ", ".join(["?"] * len(cols))
    )
    conn.executemany(sql, [tuple(row[col] for col in cols) for row in rows])


def connect_with(*loaders):
    conn = sqlite3.connect(":memory:")
    create_marts(conn)
    for loader in loaders:
        loader(conn)
    conn.commit()
    return conn


def load_clean(conn):
    insert(conn, "dim_customers", CUSTOMERS_OK)
    insert(conn, "dim_products", PRODUCTS_OK)
    insert(conn, "fct_orders", FACTS_OK)


def load_dirty(conn):
    """Valid mart rows plus planted problems. Duplicate keys are not referenced
    by facts, so joins in the other checks do not fan out."""
    load_clean(conn)

    duplicate_customer = {
        "customer_id": 99,
        "customer_name": "Casey Kim",
        "country": "Canada",
        "segment": "Enterprise",
        "signup_date": "2024-02-02",
        "cohort_month": "2024-02",
    }
    insert(
        conn,
        "dim_customers",
        [
            duplicate_customer,
            dict(duplicate_customer),
            {
                "customer_id": 3,
                "customer_name": None,
                "country": None,
                "segment": None,
                "signup_date": None,
                "cohort_month": None,
            },
            {
                "customer_id": 6,
                "customer_name": "   ",
                "country": "United States",
                "segment": "Consumer",
                "signup_date": "2024-04-01",
                "cohort_month": "2024-04",
            },
            {
                "customer_id": 4,
                "customer_name": "Nadia Rossi",
                "country": "Narnia",
                "segment": "VIP",
                "signup_date": "2020-05-05",
                "cohort_month": "2020-05",
            },
            {
                "customer_id": 5,
                "customer_name": "Omar Silva",
                "country": "Canada",
                "segment": "Enterprise",
                "signup_date": "2024-06-01",
                "cohort_month": "2024-08",
            },
        ],
    )

    duplicate_product = {
        "product_id": 99,
        "product_name": "Books Item 0099",
        "category": "Books",
        "price": 10.0,
        "cost": 6.0,
        "unit_margin": 4.0,
        "margin_pct": 0.4,
    }
    insert(
        conn,
        "dim_products",
        [
            duplicate_product,
            dict(duplicate_product),
            {
                "product_id": 3,
                "product_name": None,
                "category": None,
                "price": None,
                "cost": None,
                "unit_margin": None,
                "margin_pct": None,
            },
            {
                "product_id": 4,
                "product_name": "Mystery Item",
                "category": "Furniture",
                "price": -5.0,
                "cost": -1.0,
                "unit_margin": 0.0,
                "margin_pct": 0.0,
            },
            {
                "product_id": 5,
                "product_name": "Electronics Item 0005",
                "category": "Electronics",
                "price": 50.0,
                "cost": 10.0,
                "unit_margin": 40.0,
                "margin_pct": 0.50,  # actual margin is 0.80
            },
        ],
    )

    insert(
        conn,
        "fct_orders",
        [
            {
                "order_item_id": 1,  # duplicates the clean line
                "order_id": 2,
                "customer_id": 2,
                "product_id": 2,
                "order_date": "2024-05-01",
                "order_month": "2024-05",
                "status": "completed",
                "quantity": 1,
                "unit_price": 20.0,
                "revenue": 20.0,
                "cost_amount": 12.0,
                "gross_profit": 8.0,
            },
            {
                "order_item_id": None,
                "order_id": None,
                "customer_id": None,
                "product_id": None,
                "order_date": None,
                "order_month": None,
                "status": None,
                "quantity": None,
                "unit_price": None,
                "revenue": None,
                "cost_amount": None,
                "gross_profit": None,
            },
            {
                "order_item_id": 4,
                "order_id": 4,
                "customer_id": 1,
                "product_id": 1,
                "order_date": "2023-12-31",
                "order_month": "2023-12",
                "status": "shipped",
                "quantity": 0,
                "unit_price": -3.0,
                "revenue": 0.0,
                "cost_amount": 0.0,
                "gross_profit": 0.0,
            },
            {
                "order_item_id": 5,
                "order_id": 5,
                "customer_id": 999,
                "product_id": 1,
                "order_date": "2024-07-01",
                "order_month": "2024-07",
                "status": "completed",
                "quantity": 1,
                "unit_price": 10.0,
                "revenue": 99.0,
                "cost_amount": 68.0,
                "gross_profit": 31.0,
            },
            {
                "order_item_id": 6,
                "order_id": 6,
                "customer_id": 1,
                "product_id": 999,
                "order_date": "2024-07-02",
                "order_month": "2024-08",
                "status": "completed",
                "quantity": 1,
                "unit_price": 10.0,
                "revenue": 10.0,
                "cost_amount": 10.0,
                "gross_profit": 0.0,
            },
            {
                "order_item_id": 7,
                "order_id": 7,
                "customer_id": 2,
                "product_id": 2,
                "order_date": "2024-02-01",
                "order_month": "2024-02",
                "status": "returned",
                "quantity": 3,
                "unit_price": 10.0,
                "revenue": 30.0,
                "cost_amount": 36.0,
                "gross_profit": 0.0,  # quantity * price - quantity * cost = -6
            },
        ],
    )


def _by_name(results):
    return {result["name"]: result for result in results}


def test_catalog_matches_the_quality_sql_files():
    names = [check["name"] for check in quality.CHECKS]
    assert names == list(EXPECTED_VIOLATIONS)
    assert len(names) == len(set(names))
    assert {check["category"] for check in quality.CHECKS} <= set(quality.CATEGORIES)


def test_parse_check_rejects_a_file_without_headers():
    with pytest.raises(ValueError) as caught:
        quality.parse_check("SELECT 1", origin="broken.sql")
    assert "broken.sql" in str(caught.value)
    assert "name" in str(caught.value)


def test_clean_mart_passes():
    conn = connect_with(load_clean)
    try:
        results = quality.run_checks(conn)
    finally:
        conn.close()
    failed = [result for result in results if not result["passed"]]
    assert failed == [], quality.format_report(results)


def test_empty_marts_fail_only_the_completeness_check():
    conn = connect_with()
    try:
        results = quality.run_checks(conn)
    finally:
        conn.close()
    by_name = _by_name(results)
    assert by_name["marts.not_empty"]["violations"] == 3
    assert by_name["marts.not_empty"]["passed"] is False
    others = [result for result in results if result["name"] != "marts.not_empty"]
    assert all(result["passed"] for result in others)


def test_missing_tables_fail_every_check():
    conn = sqlite3.connect(":memory:")
    try:
        results = quality.run_checks(conn)
    finally:
        conn.close()
    assert results
    assert all(result["error"] for result in results)
    assert all(not result["passed"] for result in results)


def test_null_primary_keys_are_not_treated_as_duplicates():
    """SQLite GROUP BY lumps NULLs into one bucket. The duplicate checks must
    ignore those rows so the null checks stay the ones that count them."""
    conn = connect_with()
    try:
        insert(
            conn,
            "dim_customers",
            [
                {
                    "customer_id": None,
                    "customer_name": "Alex Smith",
                    "country": "United States",
                    "segment": "Consumer",
                    "signup_date": "2024-01-01",
                    "cohort_month": "2024-01",
                },
                {
                    "customer_id": None,
                    "customer_name": "Sam Muller",
                    "country": "Germany",
                    "segment": "SMB",
                    "signup_date": "2024-02-01",
                    "cohort_month": "2024-02",
                },
            ],
        )
        insert(
            conn,
            "dim_products",
            [
                {
                    "product_id": None,
                    "product_name": "A",
                    "category": "Books",
                    "price": 10.0,
                    "cost": 4.0,
                    "unit_margin": 6.0,
                    "margin_pct": 0.6,
                },
                {
                    "product_id": None,
                    "product_name": "B",
                    "category": "Books",
                    "price": 10.0,
                    "cost": 4.0,
                    "unit_margin": 6.0,
                    "margin_pct": 0.6,
                },
            ],
        )
        insert(
            conn,
            "fct_orders",
            [
                {
                    "order_item_id": None,
                    "order_id": 1,
                    "customer_id": 1,
                    "product_id": 1,
                    "order_date": "2024-03-01",
                    "order_month": "2024-03",
                    "status": "completed",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "revenue": 10.0,
                    "cost_amount": 4.0,
                    "gross_profit": 6.0,
                },
                {
                    "order_item_id": None,
                    "order_id": 2,
                    "customer_id": 1,
                    "product_id": 1,
                    "order_date": "2024-03-02",
                    "order_month": "2024-03",
                    "status": "completed",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "revenue": 10.0,
                    "cost_amount": 4.0,
                    "gross_profit": 6.0,
                },
            ],
        )
        duplicate_checks = [
            check for check in quality.CHECKS if check["category"] == "duplicate"
        ]
        results = quality.run_checks(conn, checks=duplicate_checks)
    finally:
        conn.close()
    assert all(result["passed"] for result in results), quality.format_report(results)


def test_impossible_calendar_dates_fail_the_range_check():
    """SQLite date('2024-02-31') is 2024-03-02, which is inside the window.
    The stored text still has to be rejected."""
    conn = connect_with()
    try:
        insert(
            conn,
            "dim_customers",
            [
                {
                    "customer_id": 1,
                    "customer_name": "Alex Smith",
                    "country": "United States",
                    "segment": "Consumer",
                    "signup_date": "2024-02-31",
                    "cohort_month": "2024-02",
                }
            ],
        )
        insert(conn, "dim_products", PRODUCTS_OK[:1])
        insert(
            conn,
            "fct_orders",
            [
                {
                    "order_item_id": 1,
                    "order_id": 1,
                    "customer_id": 1,
                    "product_id": 1,
                    "order_date": "2024-02-31",
                    "order_month": "2024-02",
                    "status": "pending",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "revenue": 100.0,
                    "cost_amount": 68.0,
                    "gross_profit": 32.0,
                }
            ],
        )
        results = quality.run_checks(conn)
    finally:
        conn.close()
    by_name = _by_name(results)
    failed = {result["name"] for result in results if not result["passed"]}
    assert failed == {"dim_customers.domain", "fct_orders.domain"}
    assert by_name["dim_customers.domain"]["violations"] == 1
    assert by_name["fct_orders.domain"]["violations"] == 1
    assert by_name["dim_customers.domain"]["sample"][0]["issue"] == "signup_date"
    assert by_name["fct_orders.domain"]["sample"][0]["issue"] == "order_date"


def test_non_positive_surrogate_keys_fail_the_range_check():
    conn = connect_with(load_clean)
    try:
        insert(
            conn,
            "dim_customers",
            [
                {
                    "customer_id": 0,
                    "customer_name": "Zero Key",
                    "country": "France",
                    "segment": "SMB",
                    "signup_date": "2024-05-01",
                    "cohort_month": "2024-05",
                }
            ],
        )
        results = quality.run_checks(conn)
    finally:
        conn.close()
    by_name = _by_name(results)
    assert by_name["dim_customers.domain"]["violations"] == 1
    assert by_name["dim_customers.domain"]["sample"][0]["issue"] == "customer_id"
    others = [
        result for result in results if result["name"] != "dim_customers.domain"
    ]
    assert all(result["passed"] for result in others)


def test_dirty_sample_reports_every_planted_issue():
    conn = connect_with(load_dirty)
    try:
        results = quality.run_checks(conn)
    finally:
        conn.close()

    by_name = _by_name(results)
    actual = {name: by_name[name]["violations"] for name in EXPECTED_VIOLATIONS}
    assert actual == EXPECTED_VIOLATIONS, quality.format_report(results)

    summary = quality.summarize(results)
    # README quotes this measurement.
    assert summary["checks"] == 17
    assert summary["failed"] == 16
    assert summary["violations"] == 48
    assert summary["by_category"]["null"]["violations"] == 24
    assert summary["by_category"]["duplicate"]["violations"] == 3
    assert summary["by_category"]["range"]["violations"] == 11
    assert summary["by_category"]["consistency"]["violations"] == 7
    assert summary["by_category"]["referential"]["violations"] == 3

    assert by_name["fct_orders.customer_fk"]["sample"][0]["customer_id"] == 999
    assert by_name["fct_orders.product_fk"]["sample"][0]["product_id"] == 999
    assert by_name["fct_orders.order_item_id_unique"]["sample"][0]["row_count"] == 2


def test_cli_missing_warehouse(tmp_path, capsys):
    code = quality.main(str(tmp_path / "missing.sqlite"))
    assert code == 1
    assert "No warehouse" in capsys.readouterr().out


def test_cli_clean_warehouse_exits_zero(tmp_path, capsys):
    db_path = tmp_path / "warehouse.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        create_marts(conn)
        load_clean(conn)
        conn.commit()
    finally:
        conn.close()
    assert quality.main(str(db_path)) == 0
    out = capsys.readouterr().out
    assert "17 checks, 0 failed, 0 violations" in out


def test_cli_dirty_warehouse_exits_nonzero(tmp_path, capsys):
    db_path = tmp_path / "warehouse.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        create_marts(conn)
        load_dirty(conn)
        conn.commit()
    finally:
        conn.close()
    assert quality.main(str(db_path)) == 1
    out = capsys.readouterr().out
    assert "16 failed, 48 violations" in out
    assert "violations by category: null 24, duplicate 3, range 11, referential 3, consistency 7" in out


def test_seeded_pipeline_marts_pass_and_analysis_still_runs(capsys):
    import run_pipeline

    run_pipeline.main()
    out = capsys.readouterr().out
    assert "[5/6] Data quality checks" in out
    assert "17 checks, 0 failed, 0 violations" in out
    assert "wrote outputs/insights.md" in out

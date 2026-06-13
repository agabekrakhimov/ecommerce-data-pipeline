"""Run the business-question SQL against the marts, print a summary, and write
outputs/insights.md plus SVG charts.

Demonstrates analytical SQL with JOINs and window functions (LAG for
month-over-month change, running cumulative SUM, RANK for product leaderboard,
and SUM() OVER () for share-of-total), plus a signup-cohort retention curve.
"""

import os
import sqlite3

import svg_charts

BASE = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE, "warehouse.sqlite")
OUT_DIR = os.path.join(BASE, "outputs")
CHART_DIR = os.path.join(OUT_DIR, "charts")


def q(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _month_index(ym):
    y, m = ym.split("-")
    return int(y) * 12 + int(m)


# --------------------------------------------------------------------------
# Business questions
# --------------------------------------------------------------------------

def monthly_revenue(conn):
    return q(
        conn,
        """
        SELECT
            order_month,
            ROUND(SUM(revenue), 2)                                      AS revenue,
            ROUND(SUM(revenue)
                  - LAG(SUM(revenue)) OVER (ORDER BY order_month), 2)   AS mom_change,
            ROUND(SUM(SUM(revenue)) OVER (ORDER BY order_month), 2)     AS cumulative_revenue
        FROM fct_orders
        WHERE status = 'completed'
        GROUP BY order_month
        ORDER BY order_month
        """,
    )


def top_products(conn, limit=10):
    return q(
        conn,
        """
        SELECT
            p.product_name,
            p.category,
            ROUND(SUM(f.revenue), 2)                          AS revenue,
            SUM(f.quantity)                                   AS units,
            RANK() OVER (ORDER BY SUM(f.revenue) DESC)        AS revenue_rank
        FROM fct_orders f
        JOIN dim_products p ON p.product_id = f.product_id
        WHERE f.status = 'completed'
        GROUP BY p.product_id
        ORDER BY revenue DESC
        LIMIT ?
        """,
        (limit,),
    )


def revenue_by_segment(conn):
    return q(
        conn,
        """
        SELECT
            c.segment,
            ROUND(SUM(f.revenue), 2)                                       AS revenue,
            COUNT(DISTINCT f.order_id)                                     AS orders,
            ROUND(SUM(f.revenue) * 100.0 / SUM(SUM(f.revenue)) OVER (), 1) AS pct_of_revenue
        FROM fct_orders f
        JOIN dim_customers c ON c.customer_id = f.customer_id
        WHERE f.status = 'completed'
        GROUP BY c.segment
        ORDER BY revenue DESC
        """,
    )


def revenue_by_country(conn, limit=5):
    return q(
        conn,
        """
        SELECT
            c.country,
            ROUND(SUM(f.revenue), 2)        AS revenue,
            COUNT(DISTINCT f.order_id)      AS orders
        FROM fct_orders f
        JOIN dim_customers c ON c.customer_id = f.customer_id
        WHERE f.status = 'completed'
        GROUP BY c.country
        ORDER BY revenue DESC
        LIMIT ?
        """,
        (limit,),
    )


def order_value_stats(conn):
    overall = q(
        conn,
        """
        SELECT
            COUNT(DISTINCT order_id)                          AS orders,
            ROUND(SUM(revenue), 2)                            AS total_revenue,
            ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 2) AS aov
        FROM fct_orders
        WHERE status = 'completed'
        """,
    )[0]
    by_segment = q(
        conn,
        """
        SELECT
            c.segment,
            ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 2) AS aov
        FROM fct_orders f
        JOIN dim_customers c ON c.customer_id = f.customer_id
        WHERE f.status = 'completed'
        GROUP BY c.segment
        ORDER BY aov DESC
        """,
    )
    return overall, by_segment


def cohort_retention(conn, max_offset=6):
    """Signup-cohort retention: share of each monthly signup cohort that placed
    a completed order N months after signup. Pooled across all cohorts that have
    a full N-month observation window."""
    rows = q(
        conn,
        """
        WITH order_cohort AS (
            SELECT DISTINCT
                f.customer_id,
                c.cohort_month,
                f.order_month
            FROM fct_orders f
            JOIN dim_customers c ON c.customer_id = f.customer_id
            WHERE f.status = 'completed'
        ),
        cohort_size AS (
            SELECT cohort_month, COUNT(DISTINCT customer_id) AS n_customers
            FROM dim_customers
            GROUP BY cohort_month
        )
        SELECT
            oc.cohort_month,
            (CAST(SUBSTR(oc.order_month, 1, 4) AS INTEGER) * 12
                 + CAST(SUBSTR(oc.order_month, 6, 2) AS INTEGER))
            - (CAST(SUBSTR(oc.cohort_month, 1, 4) AS INTEGER) * 12
                 + CAST(SUBSTR(oc.cohort_month, 6, 2) AS INTEGER))   AS months_since,
            COUNT(DISTINCT oc.customer_id)                           AS active,
            cs.n_customers
        FROM order_cohort oc
        JOIN cohort_size cs ON cs.cohort_month = oc.cohort_month
        GROUP BY oc.cohort_month, months_since
        """,
    )

    max_month = q(conn, "SELECT MAX(order_month) AS m FROM fct_orders")[0]["m"]
    max_idx = _month_index(max_month)

    # Pool active counts / cohort sizes across cohorts with a full window.
    active_by_offset = {}
    base_by_offset = {}
    cohort_size = {}
    for r in rows:
        cohort_size[r["cohort_month"]] = r["n_customers"]
    for r in rows:
        off = r["months_since"]
        if off < 0 or off > max_offset:
            continue
        if _month_index(r["cohort_month"]) + off > max_idx:
            continue
        active_by_offset[off] = active_by_offset.get(off, 0) + r["active"]

    # Denominator: cohorts observable at each offset.
    for cm, size in cohort_size.items():
        for off in range(max_offset + 1):
            if _month_index(cm) + off <= max_idx:
                base_by_offset[off] = base_by_offset.get(off, 0) + size

    curve = []
    for off in range(max_offset + 1):
        base = base_by_offset.get(off, 0)
        active = active_by_offset.get(off, 0)
        pct = round(active * 100.0 / base, 1) if base else 0.0
        curve.append({"months_since": off, "retention_pct": pct})
    return curve


def dataset_overview(conn):
    return q(
        conn,
        """
        SELECT
            (SELECT COUNT(*) FROM dim_customers)                       AS customers,
            (SELECT COUNT(*) FROM dim_products)                        AS products,
            (SELECT COUNT(DISTINCT order_id) FROM fct_orders)          AS orders,
            (SELECT COUNT(*) FROM fct_orders)                          AS order_lines,
            (SELECT MIN(order_date) FROM fct_orders)                   AS first_order,
            (SELECT MAX(order_date) FROM fct_orders)                   AS last_order
        """,
    )[0]


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def build_charts(monthly, products, segments):
    svg_charts.line_chart(
        os.path.join(CHART_DIR, "monthly_revenue_line.svg"),
        labels=[r["order_month"] for r in monthly],
        values=[r["revenue"] for r in monthly],
        title="Monthly revenue (completed orders)",
        value_prefix="$",
        color=svg_charts.ACCENT,
        label_every=2,
    )
    svg_charts.bar_chart(
        os.path.join(CHART_DIR, "top_products_bar.svg"),
        labels=[p["product_name"] for p in products],
        values=[p["revenue"] for p in products],
        title="Top 10 products by revenue",
        value_prefix="$",
        color=svg_charts.ACCENT,
    )
    svg_charts.bar_chart(
        os.path.join(CHART_DIR, "revenue_by_segment_bar.svg"),
        labels=[s["segment"] for s in segments],
        values=[s["revenue"] for s in segments],
        title="Revenue by customer segment",
        value_prefix="$",
        color=svg_charts.ACCENT_2,
    )


# --------------------------------------------------------------------------
# Insights report
# --------------------------------------------------------------------------

def _money(x):
    return "${:,.0f}".format(x)


def write_insights(overview, monthly, products, segments, countries,
                   aov_overall, aov_segment, retention):
    first_rev = monthly[0]["revenue"]
    last_rev = monthly[-1]["revenue"]
    growth = (last_rev / first_rev - 1) * 100 if first_rev else 0
    best_month = max(monthly, key=lambda r: r["revenue"])
    total_rev = aov_overall["total_revenue"]
    top_segment = segments[0]
    top_country = countries[0]
    top_product = products[0]
    ret_m1 = next((r["retention_pct"] for r in retention if r["months_since"] == 1), 0)
    ret_m3 = next((r["retention_pct"] for r in retention if r["months_since"] == 3), 0)

    lines = []
    lines.append("# Key insights\n")
    lines.append(
        "_Written by `src/analysis.py` after a pipeline run on the synthetic "
        "dataset (seed 42). Re-run the pipeline and you get the same numbers._\n"
    )

    lines.append("## Dataset")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append("| Customers | {:,} |".format(overview["customers"]))
    lines.append("| Products | {:,} |".format(overview["products"]))
    lines.append("| Orders | {:,} |".format(overview["orders"]))
    lines.append("| Order line items | {:,} |".format(overview["order_lines"]))
    lines.append("| Date range | {} -> {} |".format(
        overview["first_order"], overview["last_order"]))
    lines.append("| Total completed revenue | {} |".format(_money(total_rev)))
    lines.append("")

    lines.append("## 1. Revenue trend")
    lines.append("")
    lines.append(
        "- Revenue went from **{}** ({}) to **{}** ({}) — about "
        "**{:+.0f}%** growth over the two-year window.".format(
            _money(first_rev), monthly[0]["order_month"],
            _money(last_rev), monthly[-1]["order_month"], growth))
    lines.append(
        "- Peak month: **{}** at **{}**.".format(
            best_month["order_month"], _money(best_month["revenue"])))
    lines.append("")
    lines.append("![Monthly revenue](charts/monthly_revenue_line.svg)")
    lines.append("")

    lines.append("## 2. Top products by revenue")
    lines.append("")
    lines.append("| Rank | Product | Category | Revenue | Units |")
    lines.append("| --- | --- | --- | --- | --- |")
    for p in products:
        lines.append("| {} | {} | {} | {} | {:,} |".format(
            p["revenue_rank"], p["product_name"], p["category"],
            _money(p["revenue"]), p["units"]))
    lines.append("")
    lines.append("![Top products](charts/top_products_bar.svg)")
    lines.append("")

    lines.append("## 3. Revenue by customer segment")
    lines.append("")
    lines.append("| Segment | Revenue | Orders | % of revenue |")
    lines.append("| --- | --- | --- | --- |")
    for s in segments:
        lines.append("| {} | {} | {:,} | {:.1f}% |".format(
            s["segment"], _money(s["revenue"]), s["orders"], s["pct_of_revenue"]))
    lines.append("")
    lines.append(
        "- **{}** alone accounts for **{:.1f}%** of revenue — small segment, "
        "big share.".format(top_segment["segment"], top_segment["pct_of_revenue"]))
    lines.append("")
    lines.append("![Revenue by segment](charts/revenue_by_segment_bar.svg)")
    lines.append("")

    lines.append("## 4. Revenue by country (top 5)")
    lines.append("")
    lines.append("| Country | Revenue | Orders |")
    lines.append("| --- | --- | --- |")
    for c in countries:
        lines.append("| {} | {} | {:,} |".format(
            c["country"], _money(c["revenue"]), c["orders"]))
    lines.append("")

    lines.append("## 5. Average order value (AOV)")
    lines.append("")
    lines.append("- Overall AOV: **{}** across **{:,}** completed orders.".format(
        _money(aov_overall["aov"]), aov_overall["orders"]))
    lines.append("")
    lines.append("| Segment | AOV |")
    lines.append("| --- | --- |")
    for s in aov_segment:
        lines.append("| {} | {} |".format(s["segment"], _money(s["aov"])))
    lines.append("")

    lines.append("## 6. Signup-cohort retention")
    lines.append("")
    lines.append(
        "Of customers who signed up in a given month, what share placed another "
        "completed order N months later (pooled across cohorts with enough history):")
    lines.append("")
    lines.append("| Months since signup | Retention |")
    lines.append("| --- | --- |")
    for r in retention:
        lines.append("| {} | {:.1f}% |".format(r["months_since"], r["retention_pct"]))
    lines.append("")
    lines.append(
        "- **{:.1f}%** reorder within a month of signing up; **{:.1f}%** are "
        "still buying at the 3-month mark, then it tapers off.".format(
            ret_m1, ret_m3))
    lines.append("")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "insights.md"), "w") as f:
        f.write("\n".join(lines))

    # Return headline numbers for the console summary / README.
    return {
        "customers": overview["customers"],
        "products": overview["products"],
        "orders": overview["orders"],
        "order_lines": overview["order_lines"],
        "first_order": overview["first_order"],
        "last_order": overview["last_order"],
        "total_revenue": total_rev,
        "first_month_rev": first_rev,
        "last_month_rev": last_rev,
        "growth_pct": growth,
        "best_month": best_month,
        "top_product": top_product,
        "top_segment": top_segment,
        "top_country": top_country,
        "aov": aov_overall["aov"],
        "ret_m1": ret_m1,
        "ret_m3": ret_m3,
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        overview = dataset_overview(conn)
        monthly = monthly_revenue(conn)
        products = top_products(conn)
        segments = revenue_by_segment(conn)
        countries = revenue_by_country(conn)
        aov_overall, aov_segment = order_value_stats(conn)
        retention = cohort_retention(conn)

        build_charts(monthly, products, segments)
        kpis = write_insights(
            overview, monthly, products, segments, countries,
            aov_overall, aov_segment, retention,
        )
    finally:
        conn.close()

    print("  total revenue        {}".format(_money(kpis["total_revenue"])))
    print("  revenue growth       {:+.0f}%  ({} -> {})".format(
        kpis["growth_pct"], monthly[0]["order_month"], monthly[-1]["order_month"]))
    print("  average order value  {}".format(_money(kpis["aov"])))
    print("  top segment          {} ({:.1f}% of revenue)".format(
        kpis["top_segment"]["segment"], kpis["top_segment"]["pct_of_revenue"]))
    print("  top product          {} ({})".format(
        kpis["top_product"]["product_name"], _money(kpis["top_product"]["revenue"])))
    print("  1-month retention    {:.1f}%".format(kpis["ret_m1"]))
    print("  wrote outputs/insights.md + 3 SVG charts")
    return kpis


if __name__ == "__main__":
    main()

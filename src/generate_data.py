"""Generate a realistic, reproducible synthetic e-commerce dataset.

Pure Python standard library only (random, csv, datetime). A fixed seed makes
every run identical so the warehouse, insights and charts are reproducible.

Outputs four raw CSVs into data/raw/:
  customers.csv     customer_id, name, signup_date, country, segment
  products.csv      product_id, product_name, category, price, cost
  orders.csv        order_id, customer_id, order_date, status
  order_items.csv   order_item_id, order_id, product_id, quantity, unit_price
"""

import csv
import os
import random
from bisect import bisect_right
from datetime import date, timedelta

SEED = 42

# Roughly a 24-month window so monthly trends and cohorts are meaningful.
DATA_START = date(2024, 1, 1)
DATA_END = date(2025, 12, 31)

N_CUSTOMERS = 2000
N_PRODUCTS = 200
N_ORDERS = 20000

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# Country -> relative weight (skewed toward a few large markets).
COUNTRIES = {
    "United States": 38,
    "United Kingdom": 14,
    "Germany": 12,
    "Canada": 9,
    "France": 8,
    "Australia": 6,
    "India": 6,
    "Brazil": 4,
    "Japan": 3,
}

# Segment -> (weight, avg orders multiplier). Enterprise buys more / bigger.
SEGMENTS = {
    "Consumer": 0.62,
    "SMB": 0.28,
    "Enterprise": 0.10,
}

CATEGORIES = [
    "Electronics",
    "Home & Kitchen",
    "Clothing",
    "Sports & Outdoors",
    "Books",
    "Beauty",
    "Toys",
    "Grocery",
]

# Per-category price ranges (price_low, price_high, margin) used to keep prices
# and costs internally consistent.
CATEGORY_PRICING = {
    "Electronics": (40, 900, 0.32),
    "Home & Kitchen": (15, 320, 0.42),
    "Clothing": (12, 160, 0.55),
    "Sports & Outdoors": (18, 400, 0.45),
    "Books": (8, 45, 0.38),
    "Beauty": (6, 120, 0.60),
    "Toys": (10, 140, 0.48),
    "Grocery": (3, 60, 0.25),
}

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie",
    "Avery", "Quinn", "Noah", "Liam", "Olivia", "Emma", "Sofia", "Mateo",
    "Yuki", "Aisha", "Diego", "Mei", "Omar", "Nadia", "Lars", "Ingrid",
    "Pedro", "Chloe", "Hassan", "Priya", "Kenji", "Lucas",
]
LAST_NAMES = [
    "Smith", "Johnson", "Garcia", "Muller", "Brown", "Dubois", "Rossi",
    "Kim", "Patel", "Nguyen", "Silva", "Tanaka", "Andersen", "Lopez",
    "Khan", "Schmidt", "Wang", "Ivanov", "Cohen", "Okafor",
]


def _weighted_choice(rng, mapping):
    keys = list(mapping.keys())
    weights = list(mapping.values())
    return rng.choices(keys, weights=weights, k=1)[0]


def _random_date(rng, start, end):
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def _month_list(start, end):
    months = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _month_bounds(year, month):
    first = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return first, nxt - timedelta(days=1)


def generate_customers(rng):
    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        name = "{} {}".format(rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES))
        # Slight bias toward earlier signups so customers have time to reorder,
        # but a steady stream of new customers every month for cohort analysis.
        signup = _random_date(rng, DATA_START, DATA_END - timedelta(days=30))
        country = _weighted_choice(rng, COUNTRIES)
        segment = _weighted_choice(rng, {k: v for k, v in SEGMENTS.items()})
        customers.append(
            {
                "customer_id": cid,
                "name": name,
                "signup_date": signup.isoformat(),
                "country": country,
                "segment": segment,
            }
        )
    return customers


def generate_products(rng):
    products = []
    for pid in range(1, N_PRODUCTS + 1):
        category = rng.choice(CATEGORIES)
        low, high, margin = CATEGORY_PRICING[category]
        price = round(rng.uniform(low, high), 2)
        cost = round(price * (1 - margin) * rng.uniform(0.9, 1.1), 2)
        cost = min(cost, round(price * 0.95, 2))  # never sell below ~cost
        products.append(
            {
                "product_id": pid,
                "product_name": "{} Item {:04d}".format(category.split()[0], pid),
                "category": category,
                "price": price,
                "cost": cost,
            }
        )
    return products


def generate_orders_and_items(rng, customers, products):
    """Distribute orders across months with growth + holiday seasonality.

    Each month gets a share of total orders proportional to a linearly growing
    trend with a Q4 bump. Customers can only order on/after their signup month.
    """
    months = _month_list(DATA_START, DATA_END)
    n_months = len(months)

    # Growth trend (1.0 -> ~2.4) plus seasonal multiplier for Nov/Dec.
    weights = []
    for i, (_, m) in enumerate(months):
        trend = 1.0 + 1.4 * (i / (n_months - 1))
        seasonal = 1.55 if m in (11, 12) else (1.15 if m in (6, 7) else 1.0)
        weights.append(trend * seasonal)

    total_w = sum(weights)
    orders_per_month = [max(1, round(N_ORDERS * w / total_w)) for w in weights]

    # Precompute signup ordering for fast "eligible customer" lookup per month.
    cust_by_signup = sorted(customers, key=lambda c: c["signup_date"])
    signup_keys = [c["signup_date"] for c in cust_by_signup]

    # Weight customers by segment so Enterprise/SMB reorder more often.
    seg_order_weight = {"Consumer": 1.0, "SMB": 1.8, "Enterprise": 3.2}

    orders = []
    order_items = []
    order_id = 0
    order_item_id = 0
    product_index = list(range(len(products)))

    for (year, month), n_orders in zip(months, orders_per_month):
        first_day, last_day = _month_bounds(year, month)
        cutoff = last_day.isoformat()
        eligible_n = bisect_right(signup_keys, cutoff)
        if eligible_n == 0:
            continue
        eligible = cust_by_signup[:eligible_n]
        elig_weights = [seg_order_weight[c["segment"]] for c in eligible]

        chosen = rng.choices(eligible, weights=elig_weights, k=n_orders)
        for cust in chosen:
            order_id += 1
            order_date = _random_date(rng, first_day, last_day)
            status = rng.choices(
                ["completed", "completed", "completed", "completed",
                 "cancelled", "returned", "pending"],
                weights=[60, 0, 0, 0, 6, 5, 4],
                k=1,
            )[0]
            orders.append(
                {
                    "order_id": order_id,
                    "customer_id": cust["customer_id"],
                    "order_date": order_date.isoformat(),
                    "status": status,
                }
            )

            # 1-5 line items; Enterprise orders skew larger.
            seg = cust["segment"]
            if seg == "Enterprise":
                n_items = rng.randint(2, 6)
            elif seg == "SMB":
                n_items = rng.randint(1, 4)
            else:
                n_items = rng.randint(1, 3)

            picked = rng.sample(product_index, k=min(n_items, len(product_index)))
            for pidx in picked:
                product = products[pidx]
                order_item_id += 1
                qty = rng.randint(1, 4) if seg != "Enterprise" else rng.randint(1, 10)
                discount = rng.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.15])
                unit_price = round(product["price"] * (1 - discount), 2)
                order_items.append(
                    {
                        "order_item_id": order_item_id,
                        "order_id": order_id,
                        "product_id": product["product_id"],
                        "quantity": qty,
                        "unit_price": unit_price,
                    }
                )

    return orders, order_items


def _write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rng = random.Random(SEED)
    os.makedirs(RAW_DIR, exist_ok=True)

    customers = generate_customers(rng)
    products = generate_products(rng)
    orders, order_items = generate_orders_and_items(rng, customers, products)

    _write_csv(
        os.path.join(RAW_DIR, "customers.csv"),
        customers,
        ["customer_id", "name", "signup_date", "country", "segment"],
    )
    _write_csv(
        os.path.join(RAW_DIR, "products.csv"),
        products,
        ["product_id", "product_name", "category", "price", "cost"],
    )
    _write_csv(
        os.path.join(RAW_DIR, "orders.csv"),
        orders,
        ["order_id", "customer_id", "order_date", "status"],
    )
    _write_csv(
        os.path.join(RAW_DIR, "order_items.csv"),
        order_items,
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
    )

    print("  customers.csv    {:>7,} rows".format(len(customers)))
    print("  products.csv     {:>7,} rows".format(len(products)))
    print("  orders.csv       {:>7,} rows".format(len(orders)))
    print("  order_items.csv  {:>7,} rows".format(len(order_items)))


if __name__ == "__main__":
    main()

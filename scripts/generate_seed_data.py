"""
generate_seed_data.py
======================

Generates deterministic, referentially-consistent synthetic e-commerce data
using Faker and writes it to CSV files under ``seeds/``.

The module exposes pure, side-effect-free ``generate_*`` functions that
return ``pandas.DataFrame`` objects. This keeps the generation logic
testable without touching the filesystem or a database (see
``tests/test_generate_seed_data.py``). The CLI entry point (``main``) is a
thin wrapper that calls these functions and writes the results to disk.

Usage
-----
    python scripts/generate_seed_data.py [--out-dir seeds] [--seed 42]

Tables generated
-----------------
- customers.csv    (~200 rows): id, name, email, signup_date, country
- products.csv     (~50 rows):  id, name, category, unit_price
- orders.csv       (~800 rows): id, customer_id, order_date, status
- order_items.csv  (~2000 rows): id, order_id, product_id, quantity, unit_price
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_SEED = 42

N_CUSTOMERS = 200
N_PRODUCTS = 50
N_ORDERS = 800
N_ORDER_ITEMS = 2000

COUNTRIES = [
    "Brazil",
    "United States",
    "Portugal",
    "Germany",
    "United Kingdom",
    "Canada",
    "Argentina",
    "Spain",
    "France",
    "Mexico",
]

CATEGORIES = {
    "Electronics": (50.0, 1500.0),
    "Clothing": (15.0, 200.0),
    "Home & Kitchen": (10.0, 400.0),
    "Books": (8.0, 60.0),
    "Toys": (5.0, 120.0),
    "Sports": (10.0, 300.0),
    "Beauty": (5.0, 90.0),
    "Grocery": (2.0, 50.0),
}

# Weighted so that "delivered" dominates, as in a typical mature order book.
ORDER_STATUSES = ["delivered", "shipped", "processing", "pending", "cancelled"]
ORDER_STATUS_WEIGHTS = [0.55, 0.15, 0.10, 0.10, 0.10]

TODAY = date(2026, 9, 15)


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def generate_customers(n: int = N_CUSTOMERS, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Generate the ``customers`` table.

    Columns: id, name, email, signup_date, country
    """
    faker = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)

    rows = []
    used_emails: set[str] = set()
    for customer_id in range(1, n + 1):
        name = faker.name()

        # Guarantee unique, deterministic emails derived from the name + id,
        # instead of relying on Faker's internal uniqueness state (which can
        # vary between Faker versions).
        local_part = "".join(ch for ch in name.lower() if ch.isalnum())
        email = f"{local_part}{customer_id}@{faker.free_email_domain()}"
        while email in used_emails:
            email = f"{local_part}{customer_id}{rng.randint(0, 9999)}@{faker.free_email_domain()}"
        used_emails.add(email)

        # Signup dates spread across the last ~3 years.
        days_ago = rng.randint(0, 3 * 365)
        signup_date = TODAY - timedelta(days=days_ago)

        country = rng.choice(COUNTRIES)

        rows.append(
            {
                "id": customer_id,
                "name": name,
                "email": email,
                "signup_date": signup_date.isoformat(),
                "country": country,
            }
        )

    return pd.DataFrame(rows, columns=["id", "name", "email", "signup_date", "country"])


def generate_products(n: int = N_PRODUCTS, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Generate the ``products`` table.

    Columns: id, name, category, unit_price
    """
    faker = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)

    categories = list(CATEGORIES.keys())

    rows = []
    for product_id in range(1, n + 1):
        category = categories[(product_id - 1) % len(categories)]
        low, high = CATEGORIES[category]
        unit_price = round(rng.uniform(low, high), 2)

        product_name = f"{faker.word().capitalize()} {faker.word().capitalize()} ({category})"

        rows.append(
            {
                "id": product_id,
                "name": product_name,
                "category": category,
                "unit_price": unit_price,
            }
        )

    return pd.DataFrame(rows, columns=["id", "name", "category", "unit_price"])


def generate_orders(
    customers_df: pd.DataFrame,
    n: int = N_ORDERS,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Generate the ``orders`` table, referencing valid ``customer_id`` values.

    Columns: id, customer_id, order_date, status
    """
    rng = random.Random(seed)

    customer_signups = dict(zip(customers_df["id"], customers_df["signup_date"]))
    customer_ids = list(customer_signups.keys())

    rows = []
    for order_id in range(1, n + 1):
        customer_id = rng.choice(customer_ids)
        signup_date = date.fromisoformat(customer_signups[customer_id])

        # Orders always happen on or after the customer's signup date.
        max_days_span = max((TODAY - signup_date).days, 0)
        days_after_signup = rng.randint(0, max_days_span) if max_days_span > 0 else 0
        order_date = signup_date + timedelta(days=days_after_signup)

        status = rng.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0]

        rows.append(
            {
                "id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "status": status,
            }
        )

    return pd.DataFrame(rows, columns=["id", "customer_id", "order_date", "status"])


def generate_order_items(
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
    n: int = N_ORDER_ITEMS,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Generate the ``order_items`` table, referencing valid ``order_id`` and
    ``product_id`` values.

    Columns: id, order_id, product_id, quantity, unit_price

    ``unit_price`` reflects the price paid at purchase time: it is derived
    from the product's catalog price with a small random discount, which
    mimics historical pricing/promotions instead of always matching the
    product's *current* price exactly.

    Every order is guaranteed to have at least one item (the first
    ``len(orders_df)`` items are seeded one-per-order), and any remaining
    items are distributed randomly across orders.
    """
    rng = random.Random(seed)

    order_ids = orders_df["id"].tolist()
    product_ids = products_df["id"].tolist()
    product_prices = dict(zip(products_df["id"], products_df["unit_price"]))

    if n < len(order_ids):
        raise ValueError("n must be >= number of orders to guarantee referential coverage")

    # Ensure every order has at least one order item.
    assigned_order_ids = list(order_ids)
    remaining = n - len(order_ids)
    assigned_order_ids += [rng.choice(order_ids) for _ in range(remaining)]
    rng.shuffle(assigned_order_ids)

    rows = []
    for item_id, order_id in enumerate(assigned_order_ids, start=1):
        product_id = rng.choice(product_ids)
        quantity = rng.randint(1, 5)

        base_price = product_prices[product_id]
        discount_factor = rng.uniform(0.85, 1.0)
        unit_price = round(base_price * discount_factor, 2)

        rows.append(
            {
                "id": item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            }
        )

    return pd.DataFrame(
        rows, columns=["id", "order_id", "product_id", "quantity", "unit_price"]
    )


def generate_all(seed: int = DEFAULT_SEED) -> dict[str, pd.DataFrame]:
    """Generate all four tables in dependency order and return them as a dict."""
    customers_df = generate_customers(seed=seed)
    products_df = generate_products(seed=seed)
    orders_df = generate_orders(customers_df, seed=seed)
    order_items_df = generate_order_items(orders_df, products_df, seed=seed)

    return {
        "customers": customers_df,
        "products": products_df,
        "orders": orders_df,
        "order_items": order_items_df,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(out_dir: str | Path = "seeds", seed: int = DEFAULT_SEED) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    tables = generate_all(seed=seed)
    for table_name, df in tables.items():
        csv_path = out_path / f"{table_name}.csv"
        df.to_csv(csv_path, index=False)
        print(f"Wrote {len(df):>5} rows -> {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce seed data.")
    parser.add_argument("--out-dir", default="seeds", help="Directory to write CSV files into.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed.")
    args = parser.parse_args()

    main(out_dir=args.out_dir, seed=args.seed)

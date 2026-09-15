"""
Unit tests for scripts/generate_seed_data.py.

These tests exercise only the pure-Python/pandas generation functions and
never touch the filesystem or a live database, so they run anywhere
(including CI) with no external dependencies beyond the packages in
requirements.txt.
"""

from __future__ import annotations

import pandas as pd
import pytest

from generate_seed_data import (
    N_CUSTOMERS,
    N_ORDER_ITEMS,
    N_ORDERS,
    N_PRODUCTS,
    generate_all,
    generate_customers,
    generate_order_items,
    generate_orders,
    generate_products,
)

SEED = 42


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def customers_df() -> pd.DataFrame:
    return generate_customers(seed=SEED)


@pytest.fixture(scope="module")
def products_df() -> pd.DataFrame:
    return generate_products(seed=SEED)


@pytest.fixture(scope="module")
def orders_df(customers_df: pd.DataFrame) -> pd.DataFrame:
    return generate_orders(customers_df, seed=SEED)


@pytest.fixture(scope="module")
def order_items_df(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    return generate_order_items(orders_df, products_df, seed=SEED)


# ---------------------------------------------------------------------------
# Row counts
# ---------------------------------------------------------------------------


def test_customers_row_count(customers_df: pd.DataFrame) -> None:
    assert len(customers_df) == N_CUSTOMERS == 200


def test_products_row_count(products_df: pd.DataFrame) -> None:
    assert len(products_df) == N_PRODUCTS == 50


def test_orders_row_count(orders_df: pd.DataFrame) -> None:
    assert len(orders_df) == N_ORDERS == 800


def test_order_items_row_count(order_items_df: pd.DataFrame) -> None:
    assert len(order_items_df) == N_ORDER_ITEMS == 2000


# ---------------------------------------------------------------------------
# Schema / no nulls in required fields
# ---------------------------------------------------------------------------


def test_customers_columns_and_no_nulls(customers_df: pd.DataFrame) -> None:
    assert list(customers_df.columns) == ["id", "name", "email", "signup_date", "country"]
    assert customers_df.isnull().sum().sum() == 0


def test_products_columns_and_no_nulls(products_df: pd.DataFrame) -> None:
    assert list(products_df.columns) == ["id", "name", "category", "unit_price"]
    assert products_df.isnull().sum().sum() == 0


def test_orders_columns_and_no_nulls(orders_df: pd.DataFrame) -> None:
    assert list(orders_df.columns) == ["id", "customer_id", "order_date", "status"]
    assert orders_df.isnull().sum().sum() == 0


def test_order_items_columns_and_no_nulls(order_items_df: pd.DataFrame) -> None:
    assert list(order_items_df.columns) == [
        "id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ]
    assert order_items_df.isnull().sum().sum() == 0


# ---------------------------------------------------------------------------
# Primary key uniqueness
# ---------------------------------------------------------------------------


def test_customers_id_is_unique(customers_df: pd.DataFrame) -> None:
    assert customers_df["id"].is_unique


def test_products_id_is_unique(products_df: pd.DataFrame) -> None:
    assert products_df["id"].is_unique


def test_orders_id_is_unique(orders_df: pd.DataFrame) -> None:
    assert orders_df["id"].is_unique


def test_order_items_id_is_unique(order_items_df: pd.DataFrame) -> None:
    assert order_items_df["id"].is_unique


def test_customers_email_is_unique(customers_df: pd.DataFrame) -> None:
    assert customers_df["email"].is_unique


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------


def test_orders_reference_valid_customers(
    orders_df: pd.DataFrame, customers_df: pd.DataFrame
) -> None:
    valid_customer_ids = set(customers_df["id"])
    assert set(orders_df["customer_id"]).issubset(valid_customer_ids)


def test_order_items_reference_valid_orders(
    order_items_df: pd.DataFrame, orders_df: pd.DataFrame
) -> None:
    valid_order_ids = set(orders_df["id"])
    assert set(order_items_df["order_id"]).issubset(valid_order_ids)


def test_order_items_reference_valid_products(
    order_items_df: pd.DataFrame, products_df: pd.DataFrame
) -> None:
    valid_product_ids = set(products_df["id"])
    assert set(order_items_df["product_id"]).issubset(valid_product_ids)


def test_every_order_has_at_least_one_item(
    orders_df: pd.DataFrame, order_items_df: pd.DataFrame
) -> None:
    orders_with_items = set(order_items_df["order_id"])
    assert set(orders_df["id"]).issubset(orders_with_items)


def test_order_date_on_or_after_customer_signup(
    orders_df: pd.DataFrame, customers_df: pd.DataFrame
) -> None:
    merged = orders_df.merge(
        customers_df[["id", "signup_date"]], left_on="customer_id", right_on="id", suffixes=("", "_cust")
    )
    assert (pd.to_datetime(merged["order_date"]) >= pd.to_datetime(merged["signup_date"])).all()


# ---------------------------------------------------------------------------
# Value sanity checks
# ---------------------------------------------------------------------------


def test_product_unit_price_is_positive(products_df: pd.DataFrame) -> None:
    assert (products_df["unit_price"] > 0).all()


def test_order_item_quantity_is_positive(order_items_df: pd.DataFrame) -> None:
    assert (order_items_df["quantity"] > 0).all()


def test_order_item_unit_price_is_positive(order_items_df: pd.DataFrame) -> None:
    assert (order_items_df["unit_price"] > 0).all()


def test_order_status_is_valid(orders_df: pd.DataFrame) -> None:
    valid_statuses = {"pending", "processing", "shipped", "delivered", "cancelled"}
    assert set(orders_df["status"]).issubset(valid_statuses)


def test_products_category_is_nonempty_string(products_df: pd.DataFrame) -> None:
    assert (products_df["category"].str.len() > 0).all()


# ---------------------------------------------------------------------------
# Determinism (fixed seed reproducibility)
# ---------------------------------------------------------------------------


def test_generate_customers_is_deterministic() -> None:
    df1 = generate_customers(seed=SEED)
    df2 = generate_customers(seed=SEED)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_products_is_deterministic() -> None:
    df1 = generate_products(seed=SEED)
    df2 = generate_products(seed=SEED)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_orders_is_deterministic(customers_df: pd.DataFrame) -> None:
    df1 = generate_orders(customers_df, seed=SEED)
    df2 = generate_orders(customers_df, seed=SEED)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_order_items_is_deterministic(
    orders_df: pd.DataFrame, products_df: pd.DataFrame
) -> None:
    df1 = generate_order_items(orders_df, products_df, seed=SEED)
    df2 = generate_order_items(orders_df, products_df, seed=SEED)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_all_is_deterministic_end_to_end() -> None:
    result1 = generate_all(seed=SEED)
    result2 = generate_all(seed=SEED)
    for table_name in result1:
        pd.testing.assert_frame_equal(result1[table_name], result2[table_name])


def test_different_seed_changes_output(customers_df: pd.DataFrame) -> None:
    alt_customers_df = generate_customers(seed=SEED + 1)
    # Different seeds should not produce an identical set of names/emails.
    assert not customers_df["email"].equals(alt_customers_df["email"])


# ---------------------------------------------------------------------------
# generate_all() integration of the pure functions
# ---------------------------------------------------------------------------


def test_generate_all_returns_all_tables_consistently() -> None:
    tables = generate_all(seed=SEED)
    assert set(tables.keys()) == {"customers", "products", "orders", "order_items"}
    assert len(tables["customers"]) == N_CUSTOMERS
    assert len(tables["products"]) == N_PRODUCTS
    assert len(tables["orders"]) == N_ORDERS
    assert len(tables["order_items"]) == N_ORDER_ITEMS

    valid_customer_ids = set(tables["customers"]["id"])
    valid_product_ids = set(tables["products"]["id"])
    valid_order_ids = set(tables["orders"]["id"])

    assert set(tables["orders"]["customer_id"]).issubset(valid_customer_ids)
    assert set(tables["order_items"]["order_id"]).issubset(valid_order_ids)
    assert set(tables["order_items"]["product_id"]).issubset(valid_product_ids)

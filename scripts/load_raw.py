"""
load_raw.py
============

Loads the CSV files produced by ``generate_seed_data.py`` into a ``raw``
schema in PostgreSQL, using SQLAlchemy + psycopg2.

This mimics how raw ingestion is frequently done in real-world pipelines:
data lands with minimal/no typing (every column stored as TEXT) so that the
load step never fails on a schema mismatch. Typing, cleaning and renaming
happen downstream in the dbt staging layer (``dbt/models/staging``).

Connection settings are read from environment variables (see ``.env.example``
at the project root). If a ``.env`` file exists it is loaded automatically
via python-dotenv.

Usage
-----
    python scripts/load_raw.py [--seeds-dir seeds]

Requires a running PostgreSQL instance reachable with the configured
credentials (see ``docker-compose.yml``).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.types import Text

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional at runtime
    pass

RAW_SCHEMA = "raw"

# Maps CSV filename -> raw table name.
CSV_TO_TABLE = {
    "customers.csv": "raw_customers",
    "products.csv": "raw_products",
    "orders.csv": "raw_orders",
    "order_items.csv": "raw_order_items",
}


def get_connection_url() -> str:
    user = os.getenv("POSTGRES_USER", "dwh_user")
    password = os.getenv("POSTGRES_PASSWORD", "dwh_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ecommerce_dwh")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_engine() -> Engine:
    return create_engine(get_connection_url())


def ensure_schema(engine: Engine, schema: str = RAW_SCHEMA) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


def load_csv_to_raw(engine: Engine, csv_path: Path, table_name: str, schema: str = RAW_SCHEMA) -> int:
    """Load a single CSV into a raw table with all-TEXT columns.

    Returns the number of rows loaded.
    """
    df = pd.read_csv(csv_path, dtype=str)

    df.to_sql(
        table_name,
        con=engine,
        schema=schema,
        if_exists="replace",
        index=False,
        dtype={col: Text() for col in df.columns},
        method="multi",
        chunksize=500,
    )
    return len(df)


def main(seeds_dir: str | Path = "seeds") -> None:
    seeds_path = Path(seeds_dir)
    engine = get_engine()

    ensure_schema(engine)

    for csv_name, table_name in CSV_TO_TABLE.items():
        csv_path = seeds_path / csv_name
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Expected seed file not found: {csv_path}. "
                "Run scripts/generate_seed_data.py first."
            )
        n_rows = load_csv_to_raw(engine, csv_path, table_name)
        print(f"Loaded {n_rows:>5} rows -> {RAW_SCHEMA}.{table_name}")

    print("Raw load complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load seed CSVs into the raw PostgreSQL schema.")
    parser.add_argument("--seeds-dir", default="seeds", help="Directory containing the seed CSV files.")
    args = parser.parse_args()

    main(seeds_dir=args.seeds_dir)

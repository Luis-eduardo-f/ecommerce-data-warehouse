"""
run_pipeline.py
================

Cross-platform orchestration script for the full pipeline, as an alternative
to the Makefile (useful on Windows, where ``make`` is often unavailable).

Usage
-----
    python scripts/run_pipeline.py <step>

Steps
-----
    seed        Generate synthetic seed CSVs into seeds/
    up          Start the PostgreSQL container (docker compose up -d)
    down        Stop the PostgreSQL container (docker compose down)
    load        Load seed CSVs into the raw schema
    dbt-run     Run dbt models (dbt run)
    dbt-test    Run dbt tests (dbt test)
    dbt-docs    Generate and serve dbt docs
    all         seed -> up -> load -> dbt-run -> dbt-test, in order

Each step shells out to the same commands documented in the README, so this
script is a convenience wrapper, not a replacement for understanding what it
runs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}  (cwd={cwd or PROJECT_ROOT})")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def step_seed() -> None:
    run([sys.executable, "scripts/generate_seed_data.py"])


def step_up() -> None:
    run(["docker", "compose", "up", "-d"])


def step_down() -> None:
    run(["docker", "compose", "down"])


def step_load() -> None:
    run([sys.executable, "scripts/load_raw.py"])


def step_dbt_run() -> None:
    run(["dbt", "run", "--profiles-dir", "."], cwd=DBT_DIR)


def step_dbt_test() -> None:
    run(["dbt", "test", "--profiles-dir", "."], cwd=DBT_DIR)


def step_dbt_docs() -> None:
    run(["dbt", "docs", "generate", "--profiles-dir", "."], cwd=DBT_DIR)
    run(["dbt", "docs", "serve", "--profiles-dir", "."], cwd=DBT_DIR)


STEPS = {
    "seed": step_seed,
    "up": step_up,
    "down": step_down,
    "load": step_load,
    "dbt-run": step_dbt_run,
    "dbt-test": step_dbt_test,
    "dbt-docs": step_dbt_docs,
}

ALL_SEQUENCE = ["seed", "up", "load", "dbt-run", "dbt-test"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ecommerce-data-warehouse pipeline.")
    parser.add_argument(
        "step",
        choices=sorted(STEPS.keys()) + ["all"],
        help="Pipeline step to run.",
    )
    args = parser.parse_args()

    if args.step == "all":
        for step_name in ALL_SEQUENCE:
            STEPS[step_name]()
    else:
        STEPS[args.step]()


if __name__ == "__main__":
    main()

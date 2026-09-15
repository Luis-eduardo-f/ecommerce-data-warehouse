.PHONY: help venv seed up down load dbt-run dbt-test dbt-docs test pipeline

help:
	@echo "Targets:"
	@echo "  venv       Create a virtualenv and install requirements.txt"
	@echo "  seed       Generate synthetic seed CSVs into seeds/"
	@echo "  up         Start PostgreSQL via docker compose"
	@echo "  down       Stop PostgreSQL"
	@echo "  load       Load seed CSVs into the raw schema"
	@echo "  dbt-run    Run dbt models (dbt run)"
	@echo "  dbt-test   Run dbt tests (dbt test)"
	@echo "  dbt-docs   Generate and serve dbt docs"
	@echo "  test       Run the pytest suite (no DB required)"
	@echo "  pipeline   seed -> up -> load -> dbt-run -> dbt-test"

venv:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

seed:
	python scripts/generate_seed_data.py

up:
	docker compose up -d

down:
	docker compose down

load:
	python scripts/load_raw.py

dbt-run:
	cd dbt && dbt run --profiles-dir .

dbt-test:
	cd dbt && dbt test --profiles-dir .

dbt-docs:
	cd dbt && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

test:
	pytest tests/ -v

pipeline: seed up load dbt-run dbt-test

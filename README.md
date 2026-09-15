# ecommerce-data-warehouse

![tests](https://github.com/Luis-eduardo-f/ecommerce-data-warehouse/actions/workflows/tests.yml/badge.svg)
![license](https://img.shields.io/github/license/Luis-eduardo-f/ecommerce-data-warehouse)
![python](https://img.shields.io/badge/python-3.12%2B-blue)

Data warehouse analítico de e-commerce construído em **Python + dbt + PostgreSQL + Docker**, com dados sintéticos gerados via `Faker`. O projeto simula o fluxo completo de um pipeline de analytics engineering moderno: geração de dados brutos, carga em uma camada `raw` minimamente tipada, e transformação em camadas `staging` → `marts` inteiramente em SQL declarativo com **dbt**, incluindo um star schema, testes de qualidade de dados automatizados e modelos analíticos com window functions.

Este é o segundo projeto de portfólio de engenharia de dados do autor. O primeiro, **crypto-data-pipeline**, usa Python + Apache Airflow para orquestração de extração de dados de mercado; este projeto foca deliberadamente em **transformação declarativa com dbt** — uma habilidade central e muito demandada em vagas de analytics/data engineering que o outro repositório não cobre.

## Arquitetura

```text
┌─────────────────────┐
│  generate_seed_data  │   Faker, seed fixa (determinístico)
│       (Python)       │
└──────────┬───────────┘
           │  CSVs
           ▼
┌─────────────────────┐
│      seeds/*.csv      │   customers, products, orders, order_items
└──────────┬───────────┘
           │  load_raw.py (SQLAlchemy + psycopg2)
           ▼
┌───────────────────────────────────────────┐
│         PostgreSQL — schema "raw"           │
│  raw_customers · raw_products · raw_orders  │
│           raw_order_items (TEXT)            │
└──────────────────────┬──────────────────────┘
                        │  dbt source()
                        ▼
┌───────────────────────────────────────────┐
│            dbt — schema "staging"           │
│   stg_customers · stg_products · stg_orders │
│              stg_order_items                │
│   (tipagem, limpeza, renomeação de colunas)  │
└──────────────────────┬──────────────────────┘
                        │  dbt ref()
                        ▼
┌───────────────────────────────────────────┐
│             dbt — schema "marts"             │
│                                               │
│   dim_customers   dim_products                │
│          \            /                       │
│           \          /                        │
│           fact_orders  (grão: order_item)      │
│           /          \                         │
│  mart_revenue_by_month   mart_top_products      │
│      (window functions / agregações)           │
└───────────────────────────────────────────┘
```

## Camadas de dados

| Camada | Local | Conteúdo |
|---|---|---|
| **Geração** | `seeds/*.csv` | Dados sintéticos de e-commerce (clientes, produtos, pedidos, itens de pedido), gerados com `Faker` e seed fixa para reprodutibilidade. |
| **Raw** | `raw.raw_*` (Postgres) | Carga 1:1 dos CSVs, todas as colunas como `TEXT`. Simula ingestão bruta minimamente tipada, como em pipelines reais. |
| **Staging** | `dbt/models/staging` | Uma view por tabela raw: cast de tipos, trim/normalização de strings, renomeação de colunas para um padrão consistente. Primeira camada testada (`not_null`, `unique`). |
| **Marts — dimensões** | `dbt/models/marts` | `dim_customers` e `dim_products`: uma linha por entidade de negócio, enriquecidas com métricas agregadas (receita e pedidos por cliente, unidades vendidas por produto). |
| **Marts — fato** | `dbt/models/marts` | `fact_orders`: tabela fato no grão de item de pedido (`order_item_id`), com chaves estrangeiras para as dimensões e `line_total` calculado. |
| **Marts — analíticos** | `dbt/models/marts` | `mart_revenue_by_month` e `mart_top_products`: agregações e window functions (médias móveis, `RANK()`, variação percentual) prontas para consumo em BI. |

## Stack técnica

- **Geração de dados sintéticos**: Python + [Faker](https://faker.readthedocs.io/), com seed fixa (determinístico e reprodutível)
- **Carga raw**: Python + SQLAlchemy + psycopg2
- **Transformação**: [dbt](https://www.getdbt.com/) (dbt-core + dbt-postgres) — modelagem em camadas, `ref()`/`source()`, testes declarativos em YAML
- **Banco de dados**: PostgreSQL 16, via Docker Compose (volume nomeado para persistência)
- **Modelagem dimensional**: star schema (dimensões + fato no grão de item de pedido)
- **Testes**:
  - dbt: `not_null`, `unique`, `relationships`, `accepted_values` e testes singulares (reconciliação de receita, consistência de `line_total`)
  - pytest: geração de dados sintéticos (contagens, integridade referencial, determinismo), sem dependência de banco de dados
- **Orquestração local**: `Makefile` (Linux/macOS) e `scripts/run_pipeline.py` (multiplataforma, incluindo Windows)

## Estrutura do projeto

```text
ecommerce-data-warehouse/
├── seeds/                        # CSVs gerados (dados sintéticos)
├── scripts/
│   ├── generate_seed_data.py     # Geração determinística com Faker
│   ├── load_raw.py               # Carga dos CSVs no schema "raw"
│   └── run_pipeline.py           # Orquestração multiplataforma
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml.example      # Copiar para profiles.yml (git-ignored)
│   ├── models/
│   │   ├── staging/              # stg_*.sql + schema.yml (sources + testes)
│   │   └── marts/                # dim_*, fact_orders, mart_*.sql + schema.yml
│   └── tests/                    # Testes singulares (SQL) adicionais
├── tests/
│   └── test_generate_seed_data.py
├── docker-compose.yml
├── requirements.txt
├── Makefile
├── .env.example
└── LICENSE
```

## Como rodar

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose
- (opcional) `make`

### 1. Ambiente Python

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

```bash
cp .env.example .env
cp dbt/profiles.yml.example dbt/profiles.yml
```

Os valores default já funcionam com o `docker-compose.yml` fornecido; ajuste apenas se necessário.

### 3. Gerar dados sintéticos

```bash
python scripts/generate_seed_data.py
# ou: make seed
```

Gera `seeds/customers.csv` (~200 linhas), `seeds/products.csv` (~50), `seeds/orders.csv` (~800) e `seeds/order_items.csv` (~2000), com integridade referencial garantida e resultado idêntico a cada execução (seed fixa).

### 4. Subir o PostgreSQL

```bash
docker compose up -d
# ou: make up
```

### 5. Carregar a camada raw

```bash
python scripts/load_raw.py
# ou: make load
```

### 6. Rodar as transformações dbt

```bash
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
# a partir da raiz: make dbt-run / make dbt-test
```

### Pipeline completo (alternativa multiplataforma)

```bash
python scripts/run_pipeline.py all
```

### Rodar os testes Python (não exigem banco de dados)

```bash
pytest tests/ -v
# ou: make test
```

## Testes e qualidade de dados

O projeto usa testes em duas camadas, cada uma cobrindo uma responsabilidade diferente:

**1. pytest — lógica de geração de dados (`tests/test_generate_seed_data.py`)**

Roda em isolamento, sem banco de dados, validando as funções puras de `generate_seed_data.py`:

- Contagem de linhas esperada em cada tabela
- Ausência de nulos em colunas obrigatórias
- Unicidade de chaves primárias (e de e-mail em `customers`)
- Integridade referencial (`orders.customer_id` ⊆ `customers.id`, `order_items.order_id` ⊆ `orders.id`, `order_items.product_id` ⊆ `products.id`)
- Toda ordem possui ao menos um item, e a data do pedido é sempre posterior ao cadastro do cliente
- Determinismo: a mesma seed produz sempre o mesmo resultado (`pandas.testing.assert_frame_equal`)

**2. dbt — qualidade dos dados transformados (`dbt/models/**/schema.yml` + `dbt/tests/`)**

Testes genéricos declarados em YAML sobre cada modelo:

- `not_null` e `unique` em todas as chaves primárias (`customer_id`, `product_id`, `order_id`, `order_item_id`)
- `relationships` (testes de chave estrangeira) entre `stg_order_items` → `stg_orders`/`stg_products`, `stg_orders` → `stg_customers`, e entre `fact_orders` → `dim_customers`/`dim_products`
- `accepted_values` no status do pedido (`pending`, `processing`, `shipped`, `delivered`, `cancelled`)

Testes singulares (SQL customizado) em `dbt/tests/`, para regras de negócio que os testes genéricos não expressam:

- `assert_line_total_equals_quantity_times_price.sql`: garante que `line_total` em `fact_orders` é sempre `quantity * unit_price`
- `assert_revenue_reconciles_with_fact_orders.sql`: garante que a soma de `mart_revenue_by_month` bate com a soma de `fact_orders` (excluindo pedidos cancelados)

Rodar `dbt test` executa toda essa suíte contra o banco e falha o build caso qualquer regra seja violada — o mesmo princípio usado em pipelines de produção para impedir que dados quebrados cheguem às camadas de consumo.

## CI

O workflow [`.github/workflows/tests.yml`](.github/workflows/tests.yml) roda em todo push/PR para `main` e valida, sem depender de um Postgres real:

- **`pytest`**: a suíte de testes puramente Python da geração de dados sintéticos (30 testes).
- **`dbt parse`**: valida o grafo do projeto dbt (Jinja, YAML, `ref()`/`source()`) contra um `profiles.yml` descartável gerado a partir de `dbt/profiles.yml.example` — o parse nunca abre conexão com o banco.

## Exemplo

Saída real de `pytest -v` (30 testes, ambiente local, Python 3.12.10):

```text
tests/test_generate_seed_data.py::test_customers_row_count PASSED        [  3%]
tests/test_generate_seed_data.py::test_products_row_count PASSED         [  6%]
...
tests/test_generate_seed_data.py::test_generate_all_returns_all_tables_consistently PASSED [100%]

============================= 30 passed in 0.86s ==============================
```

Saída real de `dbt parse --profiles-dir <profiles descartável>` (dentro de `dbt/`):

```text
23:00:25  Running with dbt=1.12.5
23:00:25  Registered adapter: postgres=1.11.0
23:00:26  Unable to do partial parsing because saved manifest not found. Starting full parse.
23:00:27  Performance info: C:\...\dbt\target\perf_info.json
```

O `manifest.json` gerado por esse parse confirma o grafo do projeto: **9 models**, **4 sources** e **59 nodes de teste** (genéricos + singulares), todos resolvidos com sucesso sem tocar o banco de dados.

## Licença

MIT — veja [LICENSE](LICENSE).

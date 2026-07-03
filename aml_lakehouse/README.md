# AML Transaction Monitoring Pipeline

An AML transaction monitoring pipeline on synthetic bank data — PySpark for ingestion, dbt on Databricks for transformations, Airflow for orchestration.

Dataset: IBM's synthetic AML dataset (Kaggle, HI-Small — ~5M transactions, ~0.1% labeled laundering).

## Architecture

```
CSV --> PySpark ingestion --> Bronze (Delta)
                                  |
                                  v
                        dbt staging (typed, cleaned)
                                  |
                                  v
                dbt intermediate (velocity, fan-in/fan-out features)
                                  |
                                  v
                  dbt mart (risk score, flagged transactions)
                                  |
                                  v
                    Airflow: dbt run --> dbt test
```

- **Bronze** — raw CSV loaded as-is via PySpark into `workspace.aml_bronze.raw_transactions`, with ingestion metadata.
- **Silver (staging)** — `stg_transactions`: proper timestamp typing, cleaned columns.
- **Silver (intermediate)** — `int_transaction_features`: same-account flag, currency mismatch, amount discrepancy, rolling transaction count/sum, unique senders/recipients per account (window functions).
- **Gold** — `fct_flagged_transactions`: risk score and flag, built on the features that actually showed lift against the laundering label (mainly unique-senders / fan-in, after testing each feature individually — most of the intuitive ones didn't hold up).
- **Orchestration** — Airflow DAG runs `dbt run` then `dbt test` against the Databricks warehouse.

## Checks

12 dbt tests across the pipeline:

- **Source (bronze):** `is_laundering` not null and in `[0,1]`; `amount_paid` not null.
- **Staging:** `transaction_timestamp`, `from_account`, `to_account` not null; `is_laundering` not null and in `[0,1]`.
- **Gold:** `risk_score` not null and in `[0,1,2,3]`; `is_flagged` not null and in `[0,1]`.

Run with `dbt test` from `aml_lakehouse/`.

## Run it

```bash
# ingestion (Databricks notebook)
notebooks/01_ingest_bronze.py

# dbt
cd aml_lakehouse
dbt init      # databricks adapter, host/token/warehouse
dbt run
dbt test

# orchestration
docker compose up airflow-init
docker compose up -d
# UI at localhost:8080, trigger the aml_pipeline DAG
```

`dbt_profiles/`, `data/`, `.env` are gitignored — they hold local data and credentials.

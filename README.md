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
- **PySpark ETL (parallel path)** — `notebooks/02_pyspark_features.py` rebuilds the same features directly in PySpark instead of dbt SQL, transform-before-load style, and writes to `workspace.aml_silver.pyspark_transaction_features`. The main reason it exists: dbt's SQL couldn't express a real 24-hour rolling window (`RANGE BETWEEN INTERVAL ... PRECEDING` isn't supported through the Databricks dbt adapter), so the fan-in feature there was row-based (last 10 transactions) as a workaround. PySpark's `Window.rangeBetween()` handles true time-based windows natively, so this notebook has the more accurate version of that feature.

## Data flow techniques

A couple of notebooks explore patterns beyond the core pipeline, mainly as an exercise in different ways data can move through a system:

- **`notebooks/03_incremental_load.py`** — builds a deterministic row hash (`transaction_id`, via `sha2` over the key fields) and compares three loading strategies on the same table: `overwrite` (simple but re-processes everything), `append` (faster, but not idempotent — running it twice duplicates rows, demonstrated directly), and `MERGE`/upsert via `DeltaTable` (idempotent — re-running the same batch is a no-op). The merge pattern is the one that would actually be used in a scheduled, retryable pipeline.
- **`notebooks/04_multi_source_merge.py`** — joins the transaction data against two additional sources: a small hand-built country risk-rating table and a synthetic customer dimension (one row per account, with country, occupation, PEP flag, and Faker-generated names). This is mostly a technical exercise in combining multiple sources into one enriched view (two sequential left joins, fact table + two dimension tables) rather than a source of new signal — the country risk assignment is random by construction, so it shows ~0% lift against the laundering label, as expected. The point of including it is the join pattern itself, not a finding.
- **`notebooks/05_error_handling.py`** — a validation gate that checks for null account IDs, negative amounts, and null labels before letting data proceed (raises and halts on failure, which is what would fail an Airflow task rather than silently pass bad data downstream), plus a dead-letter pattern: rows that fail validation are split off into a `rejected_transactions` table with a rejection reason and timestamp instead of being dropped, so they stay inspectable.
- **`notebooks/06_streaming_pipeline.py`** — the same data split into chunks landed as JSON files, read with `spark.readStream` and written with `spark.writeStream` into a Delta table, using `trigger(availableNow=True)` so it processes whatever's currently available and stops (rather than running forever, which doesn't make sense inside a notebook). The interesting part is the checkpoint: re-running the exact same streaming query a second time doesn't reprocess or duplicate anything, because Spark tracks which files it's already consumed — idempotency comes for free here, unlike the manual `append` case in the incremental-load notebook. Airflow doesn't really have a role in a streaming setup like this; it's built around jobs that start and finish, not long-running listeners, so this one runs standalone.

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

# PySpark feature engineering, ETL-style (optional, parallel to dbt)
notebooks/02_pyspark_features.py

# data flow technique exercises (optional)
notebooks/03_incremental_load.py
notebooks/04_multi_source_merge.py
notebooks/05_error_handling.py
notebooks/06_streaming_pipeline.py

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
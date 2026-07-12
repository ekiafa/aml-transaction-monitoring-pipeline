#!/usr/bin/env python3
"""Run feature transformations from notebooks/02_pyspark_features.py.ipynb

This script attempts to use PySpark (local) if available; otherwise falls back to pandas.
"""
from __future__ import annotations
import sys
from typing import List, Dict


def run_with_pyspark(rows: List[Dict]):
    from pyspark.sql import SparkSession, functions as F

    spark = SparkSession.builder.master("local[*]").appName("pyspark-features-test").getOrCreate()
    df = spark.createDataFrame(rows)

    df = df.withColumn(
        "is_same_account",
        F.when(F.col("from_account") == F.col("to_account"), 1).otherwise(0),
    )

    # Mirror original notebook logic (may be comparing two currency columns named EUR and USD)
    df = df.withColumn(
        "is_currency_mismatch",
        F.when(F.col("EUR") != F.col("USD"), 1).otherwise(0),
    )

    # A more typical check compares two currency fields if present
    if "currency_from" in df.columns and "currency_to" in df.columns:
        df = df.withColumn(
            "is_currency_mismatch_correct",
            F.when(F.col("currency_from") != F.col("currency_to"), 1).otherwise(0),
        )

    df.show(truncate=False)
    spark.stop()


def run_with_pandas(rows: List[Dict]):
    import pandas as pd

    df = pd.DataFrame(rows)
    df["is_same_account"] = (df["from_account"] == df["to_account"]).astype(int)

    # Mirror original logic: compare EUR vs USD columns if they exist
    if "EUR" in df.columns and "USD" in df.columns:
        df["is_currency_mismatch"] = (df["EUR"] != df["USD"]).astype(int)
    else:
        df["is_currency_mismatch"] = 0

    if "currency_from" in df.columns and "currency_to" in df.columns:
        df["is_currency_mismatch_correct"] = (df["currency_from"] != df["currency_to"]).astype(int)

    print(df.to_string(index=False))


def main():
    sample = [
        {"from_account": "A", "to_account": "A", "EUR": 10, "USD": 12, "currency_from": "EUR", "currency_to": "USD"},
        {"from_account": "A", "to_account": "B", "EUR": 5, "USD": 5, "currency_from": "EUR", "currency_to": "EUR"},
        {"from_account": "C", "to_account": "C", "EUR": 0, "USD": 1, "currency_from": "USD", "currency_to": "USD"},
    ]

    try:
        import pyspark  # type: ignore

        print("Running with PySpark (local)")
        run_with_pyspark(sample)
    except Exception as e:  # fall back to pandas
        print("PySpark not available or failed — falling back to pandas:\n", e)
        run_with_pandas(sample)


if __name__ == "__main__":
    main()

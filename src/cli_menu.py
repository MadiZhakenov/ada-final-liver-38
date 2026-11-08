# -*- coding: utf-8 -*-
"""Console menu interface."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.audit import run_audit
from src.config import PARQUET_PATH, RAW_CSV, SQLITE_PATH
from src.db_build import load_dataframe
from src.eda import run_eda
from src.enrich import enrich_registry
from src.io_load import download_raw_csv, load_and_optimize
from src.models import evaluate_models
from src.illnesses_kz import illnesses_rates_per_100k
from src.rates import rates_per_100k
from src.sql_runner import run_all_queries
from src.stats_tests import run_stat_tests
from src.survival import compare_naive_vs_km


def _load_enriched() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    download_raw_csv()
    raw, _ = load_and_optimize(RAW_CSV)
    return enrich_registry(raw)


def run_full_pipeline() -> None:
    print("1) Download / load CSV ...")
    download_raw_csv()
    raw, mem = load_and_optimize(RAW_CSV)
    print("   memory report:", mem)

    print("2) Enrich + hash IDs ...")
    df = enrich_registry(raw)

    print("3) Audit ...")
    audit = run_audit(df)
    print("   synthetic verdict:", audit["synthetic_check"]["verdict"])

    print("4) SQLite + SQL queries ...")
    load_dataframe(df, SQLITE_PATH)
    frames = run_all_queries(SQLITE_PATH)
    print(f"   executed {len(frames)} SQL queries")

    print("5) EDA + survival + rates ...")
    run_eda(df)
    print("   KM:", compare_naive_vs_km(df))
    rates_per_100k(df)
    egov_rates = illnesses_rates_per_100k()
    print(f"   egov liver ICD rows/rates: {len(egov_rates)} regions")

    print("6) Stats + models ...")
    run_stat_tests(df)
    metrics = evaluate_models(df)
    print(metrics.to_string(index=False))
    print("DONE. See reports/ and reports/figures/")


def menu() -> None:
    actions = {
        "1": ("Full pipeline", run_full_pipeline),
        "2": ("Audit only", lambda: print(run_audit(_load_enriched()))),
        "3": ("Rebuild DB + SQL", lambda: (
            load_dataframe(_load_enriched()),
            print(f"SQL results: {len(run_all_queries())}"),
        )),
        "4": ("Train models", lambda: print(evaluate_models(_load_enriched()))),
        "0": ("Exit", None),
    }
    while True:
        print("\n=== Liver Project Menu (Topic 38) ===")
        for k, (title, _) in actions.items():
            print(f" {k}. {title}")
        choice = input("Select: ").strip()
        if choice == "0":
            print("Bye")
            break
        if choice not in actions:
            print("Unknown option")
            continue
        try:
            actions[choice][1]()
        except Exception as exc:  # noqa: BLE001 — show friendly CLI errors
            print(f"[ERROR] {type(exc).__name__}: {exc}")

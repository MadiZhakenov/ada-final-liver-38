# -*- coding: utf-8 -*-
"""Console menu interface."""
from __future__ import annotations

import pandas as pd

from src.audit import run_audit
from src.config import PARQUET_PATH, RAW_CSV, SQLITE_PATH
from src.db_build import load_dataframe
from src.eda import run_eda
from src.io_load import download_raw_csv, load_and_optimize
from src.models import evaluate_models
from src.prepare import prepare_clinical
from src.rates import rates_per_100k
from src.sql_runner import run_all_queries
from src.stats_tests import run_stat_tests
from src.survival import compare_naive_vs_km


def _load_clinical() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    download_raw_csv()
    raw, _ = load_and_optimize(RAW_CSV)
    return prepare_clinical(raw)


def run_full_pipeline() -> None:
    print("1) Download / load Ashyq CSV ...")
    download_raw_csv()
    raw, mem = load_and_optimize(RAW_CSV)
    print("   memory report:", mem)

    print("2) Prepare clinical layer (no synthetic medical fields) ...")
    df = prepare_clinical(raw)

    print("3) Audit ...")
    audit = run_audit(df)
    print("   synthetic verdict:", audit["synthetic_check"]["verdict"])

    print("4) SQLite (clinical + egov illnesses) + SQL queries ...")
    load_dataframe(df, SQLITE_PATH)
    frames = run_all_queries(SQLITE_PATH)
    print(f"   executed {len(frames)} SQL queries")

    print("5) EDA + survival note + egov rates ...")
    run_eda(df)
    print("   survival:", compare_naive_vs_km(df))
    egov_rates = rates_per_100k(df)
    print(f"   egov liver ICD rates: {len(egov_rates)} regions")

    print("6) Stats + models (Ashyq clinical only) ...")
    run_stat_tests(df)
    metrics = evaluate_models(df)
    print(metrics.to_string(index=False))
    print("DONE. See reports/ and reports/figures/")


def menu() -> None:
    actions = {
        "1": ("Full pipeline", run_full_pipeline),
        "2": ("Audit only", lambda: print(run_audit(_load_clinical()))),
        "3": ("Rebuild DB + SQL", lambda: (
            load_dataframe(_load_clinical()),
            print(f"SQL results: {len(run_all_queries())}"),
        )),
        "4": ("Train models", lambda: print(evaluate_models(_load_clinical()))),
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
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {type(exc).__name__}: {exc}")

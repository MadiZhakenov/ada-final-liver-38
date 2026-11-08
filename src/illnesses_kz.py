# -*- coding: utf-8 -*-
"""KZ open-data illnesses layer filtered to liver ICD-10 codes."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.config import (
    FIGURES,
    ILLNESSES_LIVER_CSV,
    ILLNESSES_LIVER_SUMMARY,
    MIN_GROUP_SIZE,
    REGION_POPULATION,
    REPORTS,
)


def load_illnesses_liver(path: Path | None = None) -> pd.DataFrame:
    path = path or ILLNESSES_LIVER_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Missing filtered illnesses file: {path}. "
            "Run scripts/fetch_liver_illnesses.py after placing egov cookies."
        )
    df = pd.read_csv(path, dtype=str)
    df["patients_c"] = pd.to_numeric(df["patients_c"], errors="coerce").fillna(0).astype(int)
    df["icd_stem"] = df["icd10"].astype(str).str.upper().str.split(".").str[0]
    return df


def illnesses_rates_per_100k(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Aggregate D-account / hospitalization counts by region → rate per 100k."""
    df = load_illnesses_liver() if df is None else df
    agg = (
        df.groupby("region", as_index=False)["patients_c"]
        .sum()
        .rename(columns={"patients_c": "n_patients"})
    )
    agg["population"] = agg["region"].map(REGION_POPULATION)
    known = agg.dropna(subset=["population"]).copy()
    known["rate_per_100k"] = known["n_patients"] * 100_000 / known["population"]
    known = known[known["n_patients"] >= MIN_GROUP_SIZE].sort_values(
        "rate_per_100k", ascending=False
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    known.to_csv(REPORTS / "illnesses_liver_rates_per_100k.csv", index=False)

    by_stem = (
        df.groupby("icd_stem", as_index=False)["patients_c"]
        .sum()
        .rename(columns={"patients_c": "n_patients"})
        .sort_values("n_patients", ascending=False)
    )
    by_stem.to_csv(REPORTS / "illnesses_liver_by_icd_stem.csv", index=False)

    if not known.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(known["region"], known["rate_per_100k"])
        ax.set_xlabel("Patients per 100,000 population")
        ax.set_title("Liver ICD illnesses (B15–B19, K70–K77, C22) — rates per 100k")
        ax.invert_yaxis()
        FIGURES.mkdir(parents=True, exist_ok=True)
        fig.tight_layout()
        fig.savefig(FIGURES / "07_illnesses_liver_rates_per_100k.png", dpi=140)
        plt.close(fig)

    if ILLNESSES_LIVER_SUMMARY.exists():
        # keep summary next to reports for the submission pack
        summary = ILLNESSES_LIVER_SUMMARY.read_text(encoding="utf-8")
        (REPORTS / "illnesses_liver_summary.json").write_text(summary, encoding="utf-8")

    return known

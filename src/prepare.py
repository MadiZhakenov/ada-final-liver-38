# -*- coding: utf-8 -*-
"""Prepare clinical Ashyq rows for analysis — no synthetic medical fields.

Adds only a technical case_id_hash (privacy demo / DB primary key) and a
human-readable sex label derived from the real Gender column.
"""
from __future__ import annotations

import pandas as pd

from src.config import PARQUET_PATH
from src.privacy import anonymize_ids


CLINICAL_COLS = [
    "Age",
    "Gender",
    "BMI",
    "AlcoholConsumption",
    "Smoking",
    "GeneticRisk",
    "PhysicalActivity",
    "Diabetes",
    "Hypertension",
    "LiverFunctionTest",
    "Diagnosis",
]


def prepare_clinical(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in CLINICAL_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Ashyq CSV missing columns: {missing}")

    out = df[CLINICAL_COLS].copy()
    # Technical row key only — not a fabricated medical card / NOMKART.
    raw_keys = [f"CASE-{i:05d}" for i in range(len(out))]
    out["case_id_hash"] = anonymize_ids(raw_keys)
    out["sex"] = out["Gender"].map({0: "F", 1: "M"}).fillna("U")
    out["age_bin"] = pd.cut(
        out["Age"],
        bins=[0, 30, 45, 60, 120],
        labels=["≤30", "31–45", "46–60", "60+"],
        right=True,
    ).astype(str)

    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PARQUET_PATH, index=False)
    return out

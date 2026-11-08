# -*- coding: utf-8 -*-
"""Add registry-oriented fields used by SQL, survival, rates, and dashboard modules.

The Ashyq clinical CSV has no native card id, ICD-10, region, or observation dates.
This module builds those fields in a deterministic way for Cluster 7 pipeline steps.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.config import ICD10_LIVER, PARQUET_PATH, REGION_POPULATION
from src.privacy import anonymize_ids


def _pick_icd(row: pd.Series, rng: np.random.Generator) -> str:
    codes = list(ICD10_LIVER.keys())
    # Bias alcoholic code when alcohol high + diagnosis positive.
    if row.get("Diagnosis", 0) == 1 and float(row.get("AlcoholConsumption", 0)) > 15:
        return "K70"
    if row.get("Diagnosis", 0) == 0:
        return rng.choice(codes)
    return rng.choice(codes)


def enrich_registry(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = df.copy()
    n = len(out)

    # Synthetic card numbers → hashed immediately (never store raw in DB).
    raw_cards = [f"NK{202400000 + i}" for i in range(n)]
    out["NOMKART_RAW_TMP"] = raw_cards
    out["patient_id_hash"] = anonymize_ids(out["NOMKART_RAW_TMP"])
    out = out.drop(columns=["NOMKART_RAW_TMP"])

    regions = list(REGION_POPULATION.keys())
    out["region"] = rng.choice(regions, size=n)
    orgs = [f"ORG-{i:03d}" for i in range(1, 41)]
    out["organization"] = rng.choice(orgs, size=n)
    out["dispensary_group"] = rng.choice(["D1", "D2", "D3", "D4"], size=n, p=[0.35, 0.30, 0.25, 0.10])

    out["icd10"] = [_pick_icd(out.iloc[i], rng) for i in range(n)]
    out["icd10_name"] = out["icd10"].map(ICD10_LIVER)

    base = datetime(2022, 1, 1)
    starts = [base + timedelta(days=int(x)) for x in rng.integers(0, 900, size=n)]
    durations = rng.integers(30, 700, size=n)
    ends = []
    censored = []
    for i, start in enumerate(starts):
        # ~25% still under observation (censored).
        if rng.random() < 0.25:
            ends.append(pd.NaT)
            censored.append(1)
        else:
            ends.append(start + timedelta(days=int(durations[i])))
            censored.append(0)
    out["DT_BEG"] = starts
    out["DT_END"] = ends
    out["censored"] = censored
    out["sex"] = out["Gender"].map({0: "F", 1: "M"})
    out["row_id"] = np.arange(1, n + 1)

    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PARQUET_PATH, index=False)
    return out

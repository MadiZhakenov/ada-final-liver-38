# -*- coding: utf-8 -*-
"""Data quality audit + real-vs-synthetic heuristics."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.config import AUDIT_JSON, ICD10_LIVER


def _missing_report(df: pd.DataFrame) -> dict[str, float]:
    return {c: float(df[c].isna().mean()) for c in df.columns}


def _date_issues(df: pd.DataFrame) -> dict[str, int]:
    if "DT_BEG" not in df.columns or "DT_END" not in df.columns:
        return {"end_before_beg": 0, "future_dates": 0}
    beg = pd.to_datetime(df["DT_BEG"], errors="coerce")
    end = pd.to_datetime(df["DT_END"], errors="coerce")
    today = pd.Timestamp(datetime.utcnow().date())
    end_before = int(((end.notna()) & (beg.notna()) & (end < beg)).sum())
    future = int(((beg > today) | ((end.notna()) & (end > today))).sum())
    return {"end_before_beg": end_before, "future_dates": future}


def _icd_issues(df: pd.DataFrame) -> dict[str, Any]:
    if "icd10" not in df.columns:
        return {"invalid_codes": 0, "examples": []}
    valid = set(ICD10_LIVER)
    bad = df.loc[~df["icd10"].isin(valid), "icd10"]
    return {"invalid_codes": int(bad.shape[0]), "examples": bad.head(5).tolist()}


def synthetic_check(df: pd.DataFrame) -> dict[str, Any]:
    """
    Heuristic: very flat histograms + near-zero natural correlations
    suggest synthetic / engineered data.
    """
    numeric = df.select_dtypes(include=[np.number]).copy()
    # Drop identifiers / engineered flags if present.
    drop_cols = [c for c in numeric.columns if c in {"row_id", "censored"}]
    numeric = numeric.drop(columns=drop_cols, errors="ignore")

    uniformity = {}
    for col in numeric.columns:
        x = numeric[col].dropna().values
        if len(x) < 30:
            continue
        # Compare to uniform on observed range via KS.
        lo, hi = float(np.min(x)), float(np.max(x))
        if hi <= lo:
            continue
        # Approximate uniform CDF reference via ranking stretch.
        u = (x - lo) / (hi - lo)
        ks = float(stats.kstest(u, "uniform").statistic)
        uniformity[col] = {"ks_vs_uniform": round(ks, 4)}

    corr = numeric.corr(numeric_only=True).abs()
    np.fill_diagonal(corr.values, np.nan)
    mean_abs_corr = float(np.nanmean(corr.values)) if corr.size else 0.0

    # Soft verdict for report Limitations.
    flatish = sum(1 for v in uniformity.values() if v["ks_vs_uniform"] < 0.08)
    verdict = (
        "likely_engineered_or_synthetic_features"
        if mean_abs_corr < 0.08 and flatish >= max(1, len(uniformity) // 3)
        else "shows_structure_consistent_with_real_or_semi_real_data"
    )
    return {
        "mean_abs_correlation": round(mean_abs_corr, 4),
        "uniformity": uniformity,
        "verdict": verdict,
        "note": (
            "Source file is the Ashyq clinical CSV; registry-oriented fields "
            "are constructed in preprocessing for Cluster 7 analyses."
        ),
    }


def run_audit(df: pd.DataFrame) -> dict[str, Any]:
    dup_full = int(df.duplicated().sum())
    key_cols = [c for c in ["patient_id_hash", "DT_BEG", "icd10"] if c in df.columns]
    dup_key = int(df.duplicated(subset=key_cols).sum()) if key_cols else 0

    report = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "missing_rate": _missing_report(df),
        "duplicates_full": dup_full,
        "duplicates_key": dup_key,
        "date_issues": _date_issues(df),
        "icd_issues": _icd_issues(df),
        "synthetic_check": synthetic_check(df),
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

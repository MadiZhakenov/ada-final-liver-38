# -*- coding: utf-8 -*-
"""Data quality audit + real-vs-synthetic heuristics on Ashyq clinical columns."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.config import AUDIT_JSON, CLINICAL_FEATURE_NOTE


def _missing_report(df: pd.DataFrame) -> dict[str, float]:
    return {c: float(df[c].isna().mean()) for c in df.columns}


def synthetic_check(df: pd.DataFrame) -> dict[str, Any]:
    """
    Heuristic for Topic 38: flat histograms + near-zero correlations
    suggest engineered / synthetic clinical features.
    """
    numeric = df.select_dtypes(include=[np.number]).copy()
    drop_cols = [c for c in numeric.columns if c in {"row_id"}]
    numeric = numeric.drop(columns=drop_cols, errors="ignore")

    uniformity = {}
    for col in numeric.columns:
        x = numeric[col].dropna().values
        if len(x) < 30:
            continue
        lo, hi = float(np.min(x)), float(np.max(x))
        if hi <= lo:
            continue
        u = (x - lo) / (hi - lo)
        ks = float(stats.kstest(u, "uniform").statistic)
        uniformity[col] = {"ks_vs_uniform": round(ks, 4)}

    corr = numeric.corr(numeric_only=True).abs()
    np.fill_diagonal(corr.values, np.nan)
    mean_abs_corr = float(np.nanmean(corr.values)) if corr.size else 0.0

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
        "note": CLINICAL_FEATURE_NOTE,
    }


def run_audit(df: pd.DataFrame) -> dict[str, Any]:
    clinical_cols = [
        c for c in df.columns
        if c not in {"case_id_hash", "sex", "age_bin"}
    ]
    work = df[clinical_cols] if clinical_cols else df
    dup_full = int(work.duplicated().sum())
    key_cols = [c for c in ["case_id_hash"] if c in df.columns]
    dup_key = int(df.duplicated(subset=key_cols).sum()) if key_cols else 0

    report = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "missing_rate": _missing_report(df),
        "duplicates_full": dup_full,
        "duplicates_key": dup_key,
        "date_issues": {
            "end_before_beg": 0,
            "future_dates": 0,
            "note": "Ashyq CSV has no DT_BEG/DT_END; date checks not applicable.",
        },
        "icd_issues": {
            "invalid_codes": 0,
            "examples": [],
            "note": "ICD codes come from egov illnesses layer, audited separately in SQL/EDA.",
        },
        "synthetic_check": synthetic_check(work),
        "data_policy": (
            "No synthetic medical registry fields (fake NOMKART/ICD/region/dates). "
            "Analysis uses Ashyq clinical CSV + real egov illnesses aggregates."
        ),
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report

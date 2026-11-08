# -*- coding: utf-8 -*-
"""Naive mean duration vs Kaplan–Meier with censoring."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from lifelines import KaplanMeierFitter

from src.config import FIGURES, REPORTS


def observation_duration_days(df: pd.DataFrame, censor_date: str = "2024-12-31") -> pd.DataFrame:
    work = df.copy()
    work["DT_BEG"] = pd.to_datetime(work["DT_BEG"])
    work["DT_END"] = pd.to_datetime(work["DT_END"])
    end = work["DT_END"].fillna(pd.Timestamp(censor_date))
    work["duration_days"] = (end - work["DT_BEG"]).dt.days.clip(lower=1)
    work["event"] = (work["censored"] == 0).astype(int)
    return work


def compare_naive_vs_km(df: pd.DataFrame) -> dict:
    work = observation_duration_days(df)
    naive_mean = float(work["duration_days"].mean())

    kmf = KaplanMeierFitter()
    kmf.fit(durations=work["duration_days"], event_observed=work["event"], label="KM")
    km_median = float(kmf.median_survival_time_) if kmf.median_survival_time_ == kmf.median_survival_time_ else None

    fig, ax = plt.subplots(figsize=(8, 5))
    kmf.plot_survival_function(ax=ax)
    ax.axhline(0.5, color="gray", linestyle=":", linewidth=1)
    ax.set_title("Kaplan–Meier survival of observation spell")
    ax.set_xlabel("Days under observation")
    ax.set_ylabel("P(still observed)")
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig_path = FIGURES / "05_kaplan_meier.png"
    fig.tight_layout()
    fig.savefig(fig_path, dpi=140)
    plt.close(fig)

    summary = {
        "naive_mean_days": round(naive_mean, 2),
        "km_median_days": None if km_median is None else round(km_median, 2),
        "n": int(len(work)),
        "n_censored": int((work["event"] == 0).sum()),
        "figure": str(fig_path),
        "note": "Naive mean ignores censoring; KM accounts for patients still on registry.",
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(REPORTS / "survival_summary.csv", index=False)
    return summary

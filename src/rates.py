# -*- coding: utf-8 -*-
"""Rates per 100,000 population by region."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.config import FIGURES, MIN_GROUP_SIZE, REGION_POPULATION, REPORTS


def rates_per_100k(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby("region").size().rename("n_cases").reset_index()
    counts["population"] = counts["region"].map(REGION_POPULATION)
    counts = counts.dropna(subset=["population"])
    counts["rate_per_100k"] = counts["n_cases"] * 100_000 / counts["population"]
    # Hide tiny cells.
    counts = counts[counts["n_cases"] >= MIN_GROUP_SIZE].sort_values("rate_per_100k", ascending=False)
    REPORTS.mkdir(parents=True, exist_ok=True)
    counts.to_csv(REPORTS / "rates_per_100k.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(counts["region"], counts["rate_per_100k"])
    ax.set_xlabel("Cases per 100,000 population")
    ax.set_title("Regional rates per 100,000 (approximate population)")
    ax.invert_yaxis()
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "06_rates_per_100k.png", dpi=140)
    plt.close(fig)
    return counts

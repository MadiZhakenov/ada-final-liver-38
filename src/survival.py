# -*- coding: utf-8 -*-
"""Observation-duration analysis.

Ashyq clinical CSV has no DT_BEG / DT_END / censoring flags.
We do NOT invent medical follow-up spells. This module records the limitation.
"""
from __future__ import annotations

import pandas as pd

from src.config import FIGURES, REPORTS


def compare_naive_vs_km(df: pd.DataFrame) -> dict:
    """Return N/A summary — Kaplan–Meier needs real observation spells."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "not_applicable",
        "n_rows_clinical": int(len(df)),
        "naive_mean_days": None,
        "km_median_days": None,
        "n_censored": None,
        "note": (
            "Ashyq Liver_disease_data.csv has no registry observation dates "
            "(DT_BEG/DT_END) or censoring flags. Per instructor guidance we do "
            "not synthesize medical follow-up spells. Kaplan–Meier vs naive "
            "duration is therefore not computed. Regional volume uses real "
            "egov illnesses data instead."
        ),
    }
    pd.DataFrame([summary]).to_csv(REPORTS / "survival_summary.csv", index=False)

    # Placeholder figure explaining the skip (keeps report figure set stable).
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    ax.text(
        0.5,
        0.5,
        "Kaplan–Meier not computed\n"
        "(Ashyq CSV has no observation dates; no synthetic spells)",
        ha="center",
        va="center",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "05_kaplan_meier.png", dpi=140)
    plt.close(fig)
    return summary

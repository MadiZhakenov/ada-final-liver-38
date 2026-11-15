# -*- coding: utf-8 -*-
"""EDA on real Ashyq clinical data + egov ICD volume charts."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import FIGURES, MIN_GROUP_SIZE, REPORTS
from src.illnesses_kz import load_illnesses_liver


def _save(fig: plt.Figure, name: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_target_balance(df: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df, x="Diagnosis", ax=ax, hue="Diagnosis", legend=False)
    ax.set_title("Diagnosis class balance (0=no, 1=yes) — Ashyq clinical")
    ax.set_xlabel("Diagnosis")
    ax.set_ylabel("Count")
    return _save(fig, "01_diagnosis_balance.png")


def plot_risk_boxplots(df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, col in zip(axes, ["BMI", "AlcoholConsumption", "LiverFunctionTest"]):
        sns.boxplot(data=df, x="Diagnosis", y=col, ax=ax)
        ax.set_title(col)
    fig.suptitle("Clinical factors by diagnosis (Ashyq)")
    return _save(fig, "02_risk_boxplots.png")


def plot_corr(df: pd.DataFrame) -> Path:
    cols = [
        "Age", "Gender", "BMI", "AlcoholConsumption", "Smoking", "GeneticRisk",
        "PhysicalActivity", "Diabetes", "Hypertension", "LiverFunctionTest", "Diagnosis",
    ]
    corr = df[cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=False, cmap="vlag", center=0, ax=ax)
    ax.set_title("Correlation heatmap (Ashyq clinical features)")
    return _save(fig, "03_correlation.png")


def plot_egov_icd_volume(illnesses: pd.DataFrame | None = None) -> tuple[pd.DataFrame, Path]:
    """ICD-stem patient volume from real egov illnesses (no synthetic dates)."""
    df = load_illnesses_liver() if illnesses is None else illnesses
    by_stem = (
        df.groupby("icd_stem", as_index=False)["patients_c"]
        .sum()
        .rename(columns={"patients_c": "n_patients"})
        .sort_values("n_patients", ascending=False)
    )
    by_stem = by_stem[by_stem["n_patients"] >= MIN_GROUP_SIZE]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(by_stem["icd_stem"], by_stem["n_patients"])
    ax.set_title("Egov liver ICD volume by code stem (real open data)")
    ax.set_xlabel("ICD-10 stem")
    ax.set_ylabel("Patients (sum)")
    ax.tick_params(axis="x", rotation=45)
    path = _save(fig, "04_egov_icd_volume.png")

    REPORTS.mkdir(parents=True, exist_ok=True)
    by_stem.to_csv(REPORTS / "egov_icd_volume.csv", index=False)
    # Keep legacy filename empty-ish note for old refs
    note = pd.DataFrame(
        [{
            "note": (
                "Ashyq clinical CSV has no observation dates; monthly registry "
                "time series are not fabricated. See egov_icd_volume.csv instead."
            )
        }]
    )
    note.to_csv(REPORTS / "monthly_registry_series.csv", index=False)
    return by_stem, path


def run_eda(df: pd.DataFrame) -> dict:
    paths = {
        "balance": str(plot_target_balance(df)),
        "boxplots": str(plot_risk_boxplots(df)),
        "corr": str(plot_corr(df)),
    }
    _, egov_path = plot_egov_icd_volume()
    paths["egov_icd"] = str(egov_path)
    return paths

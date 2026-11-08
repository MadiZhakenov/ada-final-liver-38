# -*- coding: utf-8 -*-
"""EDA plots + monthly registry time series."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import FIGURES, MIN_GROUP_SIZE


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
    ax.set_title("Diagnosis class balance (0=no, 1=yes)")
    ax.set_xlabel("Diagnosis")
    ax.set_ylabel("Count")
    return _save(fig, "01_diagnosis_balance.png")


def plot_risk_boxplots(df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, col in zip(axes, ["BMI", "AlcoholConsumption", "LiverFunctionTest"]):
        sns.boxplot(data=df, x="Diagnosis", y=col, ax=ax)
        ax.set_title(col)
    fig.suptitle("Clinical factors by diagnosis")
    return _save(fig, "02_risk_boxplots.png")


def plot_corr(df: pd.DataFrame) -> Path:
    cols = [
        "Age", "Gender", "BMI", "AlcoholConsumption", "Smoking", "GeneticRisk",
        "PhysicalActivity", "Diabetes", "Hypertension", "LiverFunctionTest", "Diagnosis",
    ]
    corr = df[cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=False, cmap="vlag", center=0, ax=ax)
    ax.set_title("Correlation heatmap (clinical features)")
    return _save(fig, "03_correlation.png")


def monthly_registry_series(df: pd.DataFrame) -> tuple[pd.DataFrame, Path]:
    work = df.copy()
    work["DT_BEG"] = pd.to_datetime(work["DT_BEG"])
    work["DT_END"] = pd.to_datetime(work["DT_END"])
    work["beg_ym"] = work["DT_BEG"].dt.to_period("M").astype(str)
    work["end_ym"] = work["DT_END"].dt.to_period("M").astype(str)

    started = work.groupby(["beg_ym", "icd10", "region"], dropna=False).size().reset_index(name="started")
    started = started.rename(columns={"beg_ym": "ym"})
    closed = (
        work.dropna(subset=["DT_END"])
        .groupby(["end_ym", "icd10", "region"], dropna=False)
        .size()
        .reset_index(name="closed")
        .rename(columns={"end_ym": "ym"})
    )
    series = started.merge(closed, on=["ym", "icd10", "region"], how="outer").fillna(0)
    series["started"] = series["started"].astype(int)
    series["closed"] = series["closed"].astype(int)

    # Aggregate national monthly for plot (hide tiny groups elsewhere in tables).
    nat = series.groupby("ym", as_index=False)[["started", "closed"]].sum().sort_values("ym")
    nat["started_roll3"] = nat["started"].rolling(3, min_periods=1).mean()
    nat["closed_roll3"] = nat["closed"].rolling(3, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(nat["ym"], nat["started"], label="Started", marker="o", markersize=3)
    ax.plot(nat["ym"], nat["started_roll3"], label="Started MA(3)", linestyle="--")
    ax.plot(nat["ym"], nat["closed"], label="Closed", marker="o", markersize=3)
    ax.plot(nat["ym"], nat["closed_roll3"], label="Closed MA(3)", linestyle="--")
    ax.set_title("Monthly registry events (national)")
    ax.set_xlabel("Year-month")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    path = _save(fig, "04_monthly_registry.png")

    # Suppress tiny groups for exported detailed table.
    detailed = series.copy()
    detailed = detailed[(detailed["started"] + detailed["closed"]) >= MIN_GROUP_SIZE]
    return detailed, path


def run_eda(df: pd.DataFrame) -> dict:
    paths = {
        "balance": str(plot_target_balance(df)),
        "boxplots": str(plot_risk_boxplots(df)),
        "corr": str(plot_corr(df)),
    }
    series, ts_path = monthly_registry_series(df)
    paths["monthly"] = str(ts_path)
    series.to_csv(FIGURES.parent / "monthly_registry_series.csv", index=False)
    return paths

# -*- coding: utf-8 -*-
"""Dummy vs LogisticRegression vs RandomForest with stratified CV."""
from __future__ import annotations

import json
import time
import tracemalloc
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import FIGURES, METRICS_JSON, REPORTS

FEATURE_COLS = [
    "Age", "Gender", "BMI", "AlcoholConsumption", "Smoking", "GeneticRisk",
    "PhysicalActivity", "Diabetes", "Hypertension", "LiverFunctionTest",
]


def _build_models() -> dict[str, Any]:
    num_cols = FEATURE_COLS
    pre = ColumnTransformer(
        [("num", StandardScaler(), num_cols)],
        remainder="drop",
    )
    return {
        "dummy": Pipeline([
            ("pre", pre),
            ("clf", DummyClassifier(strategy="most_frequent")),
        ]),
        "logreg": Pipeline([
            ("pre", pre),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]),
        "rf": Pipeline([
            ("pre", "passthrough"),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced_subsample",
                n_jobs=-1,
            )),
        ]),
    }


def _predict_scores(model, X, y, cv) -> tuple[np.ndarray, np.ndarray]:
    """Return out-of-fold labels and positive-class scores when available."""
    if hasattr(model.named_steps["clf"], "predict_proba"):
        proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba")
        scores = proba[:, 1]
        preds = (scores >= 0.5).astype(int)
        return preds, scores
    preds = cross_val_predict(model, X, y, cv=cv, method="predict")
    return preds, preds.astype(float)


def evaluate_models(df: pd.DataFrame, n_splits: int = 5) -> pd.DataFrame:
    X = df[FEATURE_COLS].copy()
    y = df["Diagnosis"].astype(int).values
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    models = _build_models()
    rows = []
    score_store = {}

    for name, model in models.items():
        tracemalloc.start()
        t0 = time.perf_counter()
        preds, scores = _predict_scores(model, X, y, cv)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Dummy most_frequent may have constant scores.
        try:
            auc = float(roc_auc_score(y, scores))
        except ValueError:
            auc = float("nan")
        f1 = float(f1_score(y, preds))
        rows.append({
            "model": name,
            "roc_auc": None if auc != auc else round(auc, 4),
            "f1": round(f1, 4),
            "seconds": round(elapsed, 4),
            "peak_memory_mb": round(peak / (1024 ** 2), 4),
        })
        score_store[name] = (y, scores)

    metrics = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(REPORTS / "model_metrics.csv", index=False)
    METRICS_JSON.write_text(metrics.to_json(orient="records", indent=2), encoding="utf-8")

    # Calibration curves for probabilistic models.
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot([0, 1], [0, 1], "k--", label="Perfect")
    for name in ["logreg", "rf"]:
        y_true, scores = score_store[name]
        frac_pos, mean_pred = calibration_curve(y_true, scores, n_bins=8, strategy="quantile")
        ax.plot(mean_pred, frac_pos, marker="o", label=name)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Calibration curves (OOF stratified CV)")
    ax.legend()
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / "07_calibration.png", dpi=140)
    plt.close(fig)

    # Fit logreg on full data for coefficient export.
    logreg = models["logreg"]
    logreg.fit(X, y)
    coefs = pd.DataFrame({
        "feature": FEATURE_COLS,
        "coefficient": logreg.named_steps["clf"].coef_.ravel(),
    })
    coefs["odds_ratio"] = np.exp(coefs["coefficient"])
    coefs.to_csv(REPORTS / "logreg_coefficients.csv", index=False)
    return metrics

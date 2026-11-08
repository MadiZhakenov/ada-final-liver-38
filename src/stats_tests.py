# -*- coding: utf-8 -*-
"""Chi-square, Mann–Whitney, odds ratios for risk factors."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import logit

from src.config import REPORTS


def _chi_square_binary(df: pd.DataFrame, col: str, target: str = "Diagnosis") -> dict:
    table = pd.crosstab(df[col], df[target])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    # Odds ratio for 2x2 if possible.
    or_value = None
    if table.shape == (2, 2):
        a, b = table.iloc[1, 1], table.iloc[1, 0]
        c, d = table.iloc[0, 1], table.iloc[0, 0]
        or_value = float(((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5)))
    return {
        "factor": col,
        "test": "chi-square",
        "stat": round(float(chi2), 4),
        "p_value": float(p),
        "dof": int(dof),
        "odds_ratio": None if or_value is None else round(or_value, 4),
    }


def _mannwhitney(df: pd.DataFrame, col: str, target: str = "Diagnosis") -> dict:
    a = df.loc[df[target] == 1, col].dropna()
    b = df.loc[df[target] == 0, col].dropna()
    stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {
        "factor": col,
        "test": "mannwhitney",
        "stat": round(float(stat), 4),
        "p_value": float(p),
        "dof": None,
        "odds_ratio": None,
    }


def logistic_odds_ratios(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Age", "Gender", "BMI", "AlcoholConsumption", "Smoking", "GeneticRisk",
        "PhysicalActivity", "Diabetes", "Hypertension", "LiverFunctionTest",
    ]
    formula = "Diagnosis ~ " + " + ".join(cols)
    model = logit(formula, data=df).fit(disp=False)
    params = model.params
    conf = model.conf_int()
    out = pd.DataFrame({
        "term": params.index,
        "coef": params.values,
        "odds_ratio": np.exp(params.values),
        "ci_low": np.exp(conf[0].values),
        "ci_high": np.exp(conf[1].values),
        "p_value": model.pvalues.values,
    })
    return out


def run_stat_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ["Gender", "Smoking", "GeneticRisk", "Diabetes", "Hypertension"]:
        rows.append(_chi_square_binary(df, col))
    for col in ["Age", "BMI", "AlcoholConsumption", "PhysicalActivity", "LiverFunctionTest"]:
        rows.append(_mannwhitney(df, col))
    table = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    table.to_csv(REPORTS / "stat_tests.csv", index=False)

    ors = logistic_odds_ratios(df)
    ors.to_csv(REPORTS / "logistic_odds_ratios.csv", index=False)
    summary = {
        "n_tests": int(len(table)),
        "significant_005": int((table["p_value"] < 0.05).sum()),
    }
    (REPORTS / "stat_tests_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return table

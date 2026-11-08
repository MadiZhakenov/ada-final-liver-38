# -*- coding: utf-8 -*-
"""Streamlit dashboard with region / ICD / sex / period filters."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import METRICS_JSON, PARQUET_PATH, RAW_CSV
from src.enrich import enrich_registry
from src.io_load import download_raw_csv, load_and_optimize


@st.cache_data(show_spinner=True)
def load_data() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    download_raw_csv()
    raw, _ = load_and_optimize(RAW_CSV)
    return enrich_registry(raw)


def main() -> None:
    st.set_page_config(page_title="Liver Disease Dashboard", layout="wide")
    st.title("Liver Disease Risk — Topic 38")
    st.caption("Filters: region, ICD-10 class, sex, period")

    try:
        df = load_data()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to load data: {exc}")
        return

    work = df.copy()
    work["DT_BEG"] = pd.to_datetime(work["DT_BEG"])
    work["icd_class"] = work["icd10"].astype(str).str[:3]

    regions = sorted(work["region"].dropna().unique())
    icds = sorted(work["icd_class"].dropna().unique())
    sexes = sorted(work["sex"].dropna().unique())

    c1, c2, c3, c4 = st.columns(4)
    region = c1.multiselect("Region", regions, default=regions[:5])
    icd = c2.multiselect("ICD-10 class", icds, default=icds)
    sex = c3.multiselect("Sex", sexes, default=sexes)
    min_d, max_d = work["DT_BEG"].min().date(), work["DT_BEG"].max().date()
    period = c4.date_input("Period (DT_BEG)", value=(min_d, max_d))

    mask = work["region"].isin(region) & work["icd_class"].isin(icd) & work["sex"].isin(sex)
    if isinstance(period, (list, tuple)) and len(period) == 2:
        start, end = pd.to_datetime(period[0]), pd.to_datetime(period[1])
        mask &= (work["DT_BEG"] >= start) & (work["DT_BEG"] <= end)
    filtered = work.loc[mask]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Rows", len(filtered))
    k2.metric("Diagnosis rate", f"{filtered['Diagnosis'].mean():.1%}" if len(filtered) else "n/a")
    k3.metric("Mean BMI", f"{filtered['BMI'].mean():.1f}" if len(filtered) else "n/a")
    k4.metric("Mean Alcohol", f"{filtered['AlcoholConsumption'].mean():.1f}" if len(filtered) else "n/a")

    st.subheader("Diagnosis by ICD class")
    if len(filtered):
        st.bar_chart(filtered.groupby("icd_class")["Diagnosis"].mean())
    else:
        st.warning("No rows for current filters (or groups too small).")

    st.subheader("Monthly starts")
    if len(filtered):
        tmp = filtered.copy()
        tmp["ym"] = tmp["DT_BEG"].dt.to_period("M").astype(str)
        st.line_chart(tmp.groupby("ym").size())

    st.subheader("Model metrics")
    if METRICS_JSON.exists():
        st.dataframe(pd.read_json(METRICS_JSON))
    else:
        st.info("Run full pipeline first to generate model_metrics.json")

    st.subheader("Preview")
    show_cols = [
        "patient_id_hash", "sex", "Age", "region", "icd10", "DT_BEG", "Diagnosis",
        "BMI", "AlcoholConsumption", "LiverFunctionTest",
    ]
    st.dataframe(filtered[show_cols].head(100))


if __name__ == "__main__":
    main()

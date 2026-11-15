# -*- coding: utf-8 -*-
"""Streamlit dashboard: Ashyq clinical filters + egov region/ICD filters."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import METRICS_JSON, PARQUET_PATH, RAW_CSV
from src.illnesses_kz import load_illnesses_liver
from src.io_load import download_raw_csv, load_and_optimize
from src.prepare import prepare_clinical


@st.cache_data(show_spinner=True)
def load_clinical() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    download_raw_csv()
    raw, _ = load_and_optimize(RAW_CSV)
    return prepare_clinical(raw)


@st.cache_data(show_spinner=True)
def load_egov() -> pd.DataFrame:
    return load_illnesses_liver()


def main() -> None:
    st.set_page_config(page_title="Liver Disease Dashboard", layout="wide")
    st.title("Liver Disease Risk — Topic 38")
    st.caption(
        "Two real layers: Ashyq clinical risk factors + egov illnesses (liver ICD). "
        "No synthetic patients / ICD / dates."
    )

    tab_clin, tab_egov, tab_models = st.tabs(
        ["Ashyq clinical", "Egov region / ICD", "Model metrics"]
    )

    with tab_clin:
        try:
            df = load_clinical()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to load clinical data: {exc}")
            return

        sexes = sorted(df["sex"].dropna().unique())
        age_bins = sorted(df["age_bin"].dropna().unique())
        diags = sorted(df["Diagnosis"].dropna().unique())

        c1, c2, c3 = st.columns(3)
        sex = c1.multiselect("Sex", sexes, default=sexes)
        age_bin = c2.multiselect("Age bin", age_bins, default=age_bins)
        diag = c3.multiselect("Diagnosis label", diags, default=diags)

        filtered = df[
            df["sex"].isin(sex) & df["age_bin"].isin(age_bin) & df["Diagnosis"].isin(diag)
        ]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rows", len(filtered))
        k2.metric("Diagnosis rate", f"{filtered['Diagnosis'].mean():.1%}" if len(filtered) else "n/a")
        k3.metric("Mean BMI", f"{filtered['BMI'].mean():.1f}" if len(filtered) else "n/a")
        k4.metric("Mean Alcohol", f"{filtered['AlcoholConsumption'].mean():.1f}" if len(filtered) else "n/a")

        st.subheader("Diagnosis rate by age bin")
        if len(filtered):
            st.bar_chart(filtered.groupby("age_bin")["Diagnosis"].mean())
        else:
            st.warning("No rows for current filters.")

        st.subheader("Preview")
        show_cols = [
            "case_id_hash", "sex", "Age", "age_bin", "Diagnosis",
            "BMI", "AlcoholConsumption", "LiverFunctionTest",
        ]
        st.dataframe(filtered[show_cols].head(100))

    with tab_egov:
        try:
            egov = load_egov()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to load egov illnesses: {exc}")
            return

        regions = sorted(egov["region"].dropna().unique())
        stems = sorted(egov["icd_stem"].dropna().unique())
        c1, c2 = st.columns(2)
        region = c1.multiselect("Region", regions, default=regions[:8] if len(regions) > 8 else regions)
        icd = c2.multiselect("ICD-10 stem", stems, default=stems)

        egov_f = egov[egov["region"].isin(region) & egov["icd_stem"].isin(icd)]
        st.metric("Filtered illness rows", len(egov_f))
        st.metric("Sum patients_c", int(egov_f["patients_c"].sum()) if len(egov_f) else 0)

        st.subheader("Patients by ICD stem")
        if len(egov_f):
            st.bar_chart(egov_f.groupby("icd_stem")["patients_c"].sum())
        st.subheader("Preview")
        st.dataframe(
            egov_f[["region", "icd10", "icd_name", "patients_c"]].head(100)
        )

    with tab_models:
        if METRICS_JSON.exists():
            st.dataframe(pd.read_json(METRICS_JSON))
        else:
            st.info("Run full pipeline first to generate model_metrics.json")


if __name__ == "__main__":
    main()

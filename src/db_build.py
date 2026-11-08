# -*- coding: utf-8 -*-
"""Build normalized SQLite DB from enriched dataframe."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_DIR, REGION_POPULATION, SQLITE_PATH


def _connect(db_path: Path = SQLITE_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    schema = (DB_DIR / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def load_dataframe(df: pd.DataFrame, db_path: Path = SQLITE_PATH) -> Path:
    if "patient_id_hash" not in df.columns:
        raise ValueError("Run enrichment/privacy before DB load.")

    conn = _connect(db_path)
    try:
        init_schema(conn)

        regions = sorted(REGION_POPULATION.keys())
        region_map = {}
        for i, name in enumerate(regions, start=1):
            conn.execute(
                "INSERT INTO region(region_id, region_name, population) VALUES (?, ?, ?)",
                (i, name, int(REGION_POPULATION[name])),
            )
            region_map[name] = i

        org_codes = sorted(df["organization"].astype(str).unique())
        org_map = {}
        for i, code in enumerate(org_codes, start=1):
            # Assign org to most frequent region among its rows.
            sub = df.loc[df["organization"] == code, "region"]
            region_name = sub.mode().iloc[0] if not sub.empty else regions[0]
            conn.execute(
                "INSERT INTO organization(organization_id, organization_code, region_id) VALUES (?, ?, ?)",
                (i, code, region_map[region_name]),
            )
            org_map[code] = i

        diag_rows = df[["icd10", "icd10_name"]].drop_duplicates()
        diag_map = {}
        for i, row in enumerate(diag_rows.itertuples(index=False), start=1):
            icd_class = str(row.icd10)[:3]
            conn.execute(
                "INSERT INTO diagnosis(diagnosis_id, icd10, icd10_name, icd_class) VALUES (?, ?, ?, ?)",
                (i, row.icd10, row.icd10_name, icd_class),
            )
            diag_map[row.icd10] = i

        groups = sorted(df["dispensary_group"].astype(str).unique())
        group_map = {}
        for i, g in enumerate(groups, start=1):
            conn.execute(
                "INSERT INTO dispensary_group(group_id, group_code, description) VALUES (?, ?, ?)",
                (i, g, f"Dispensary group {g}"),
            )
            group_map[g] = i

        patients = df.drop_duplicates(subset=["patient_id_hash"])
        for row in patients.itertuples(index=False):
            conn.execute(
                """
                INSERT INTO patient(
                    patient_id_hash, sex, age, bmi, alcohol_consumption, smoking,
                    genetic_risk, physical_activity, diabetes, hypertension,
                    liver_function_test, diagnosis_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.patient_id_hash,
                    row.sex,
                    int(row.Age),
                    float(row.BMI),
                    float(row.AlcoholConsumption),
                    int(row.Smoking),
                    int(row.GeneticRisk),
                    float(row.PhysicalActivity),
                    int(row.Diabetes),
                    int(row.Hypertension),
                    float(row.LiverFunctionTest),
                    int(row.Diagnosis),
                ),
            )

        for i, row in enumerate(df.itertuples(index=False), start=1):
            dt_end = None if pd.isna(row.DT_END) else pd.Timestamp(row.DT_END).strftime("%Y-%m-%d")
            dt_beg = pd.Timestamp(row.DT_BEG).strftime("%Y-%m-%d")
            conn.execute(
                """
                INSERT INTO observation(
                    observation_id, patient_id_hash, diagnosis_id, organization_id,
                    group_id, dt_beg, dt_end, censored
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    row.patient_id_hash,
                    diag_map[row.icd10],
                    org_map[str(row.organization)],
                    group_map[str(row.dispensary_group)],
                    dt_beg,
                    dt_end,
                    int(row.censored),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path

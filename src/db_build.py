# -*- coding: utf-8 -*-
"""Build normalized SQLite DB from real Ashyq clinical + egov illness layers."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_DIR, ICD10_LIVER, REGION_POPULATION, SQLITE_PATH
from src.illnesses_kz import load_illnesses_liver


def _connect(db_path: Path = SQLITE_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    schema = (DB_DIR / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def load_dataframe(clinical: pd.DataFrame, db_path: Path = SQLITE_PATH) -> Path:
    if "case_id_hash" not in clinical.columns:
        raise ValueError("Run prepare_clinical() before DB load.")

    illnesses = load_illnesses_liver()
    conn = _connect(db_path)
    try:
        init_schema(conn)

        # Regions that appear in egov or have known population.
        region_names = sorted(
            set(illnesses["region"].dropna().astype(str)) | set(REGION_POPULATION.keys())
        )
        region_map: dict[str, int] = {}
        for i, name in enumerate(region_names, start=1):
            pop = int(REGION_POPULATION.get(name, 0))
            conn.execute(
                "INSERT INTO region(region_id, region_name, population) VALUES (?, ?, ?)",
                (i, name, pop),
            )
            region_map[name] = i

        # ICD dictionary from egov rows + static liver reference names.
        diag_map: dict[str, int] = {}
        diag_rows = (
            illnesses[["icd10", "icd_name"]]
            .dropna(subset=["icd10"])
            .drop_duplicates(subset=["icd10"], keep="first")
        )
        for i, row in enumerate(diag_rows.itertuples(index=False), start=1):
            code = str(row.icd10)
            stem = code.split(".")[0].upper()
            name = str(row.icd_name) if pd.notna(row.icd_name) else ICD10_LIVER.get(stem, code)
            icd_class = stem[:1] if stem else "?"
            # Prefer letter+digits stem class like K70 / B18 / C22
            if len(stem) >= 3:
                icd_class = stem[:3]
            conn.execute(
                "INSERT INTO diagnosis(diagnosis_id, icd10, icd10_name, icd_class) VALUES (?, ?, ?, ?)",
                (i, code, name, icd_class),
            )
            diag_map[code] = i

        for row in clinical.itertuples(index=False):
            conn.execute(
                """
                INSERT INTO clinical_case(
                    case_id_hash, sex, age, age_bin, bmi, alcohol_consumption, smoking,
                    genetic_risk, physical_activity, diabetes, hypertension,
                    liver_function_test, diagnosis_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.case_id_hash,
                    row.sex,
                    int(row.Age),
                    str(row.age_bin),
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

        for i, row in enumerate(illnesses.itertuples(index=False), start=1):
            region = str(row.region)
            code = str(row.icd10)
            if region not in region_map or code not in diag_map:
                continue
            conn.execute(
                """
                INSERT INTO illness_stat(
                    stat_id, region_id, diagnosis_id, patients_c, cat, code, subcode, sdu_load_i
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    region_map[region],
                    diag_map[code],
                    int(row.patients_c),
                    None if pd.isna(row.cat) else str(row.cat),
                    None if pd.isna(row.code) else str(row.code),
                    None if pd.isna(row.subcode) else str(row.subcode),
                    None if pd.isna(row.sdu_load_i) else float(row.sdu_load_i),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return db_path

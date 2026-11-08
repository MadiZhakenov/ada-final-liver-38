# -*- coding: utf-8 -*-
"""Paths and project constants."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
DB_DIR = ROOT / "db"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"

RAW_CSV = DATA_RAW / "Liver_disease_data.csv"
PARQUET_PATH = DATA_PROCESSED / "liver_enriched.parquet"
SQLITE_PATH = DB_DIR / "liver.db"
AUDIT_JSON = REPORTS / "audit_report.json"
METRICS_JSON = REPORTS / "model_metrics.json"
MEMORY_JSON = REPORTS / "memory_report.json"

DATA_URL = "https://s3.sdu.gov.kz/magda-datasets/Liver_disease_data.csv"
DATASET_PAGE = (
    "https://ashyq.data.gov.kz/dataset/magda-ds-8ec6e917-d808-494a-b84d-177dd857d7c4/details"
)

# Approximate 2024 population by region (thousands) for rate per 100k demo.
# Replace with exact exports from https://stat.gov.kz when available.
REGION_POPULATION = {
    "Almaty city": 2200_000,
    "Astana city": 1400_000,
    "Shymkent city": 1200_000,
    "Almaty region": 1500_000,
    "Karaganda region": 1350_000,
    "East Kazakhstan": 1300_000,
    "Turkestan region": 2100_000,
    "Aktobe region": 920_000,
    "Pavlodar region": 750_000,
    "Kostanay region": 830_000,
    "Atyrau region": 700_000,
    "Mangystau region": 780_000,
    "North Kazakhstan": 530_000,
    "Zhambyl region": 1200_000,
    "West Kazakhstan": 690_000,
    "Abai region": 610_000,
}

ICD10_LIVER = {
    "K70": "Alcoholic liver disease",
    "K73": "Chronic hepatitis",
    "K74": "Fibrosis and cirrhosis",
    "K75": "Other inflammatory liver diseases",
    "K76": "Other diseases of liver",
}

MIN_GROUP_SIZE = 10


def get_salt() -> str:
    salt = os.getenv("NOMKART_SALT", "").strip()
    if not salt:
        salt = "local-default-salt-set-via-dotenv"
    return salt

# -*- coding: utf-8 -*-
"""Execute SQL file statements and return pandas DataFrames."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_DIR, REPORTS, SQLITE_PATH


def split_sql_statements(text: str) -> list[str]:
    parts = re.split(r";\s*\n", text)
    out = []
    for p in parts:
        cleaned = "\n".join(
            line for line in p.splitlines() if not line.strip().startswith("--")
        ).strip()
        if cleaned:
            out.append(cleaned)
    return out


def run_all_queries(db_path: Path = SQLITE_PATH) -> list[pd.DataFrame]:
    sql_path = DB_DIR / "queries.sql"
    statements = split_sql_statements(sql_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(db_path)
    frames: list[pd.DataFrame] = []
    try:
        for i, stmt in enumerate(statements, start=1):
            df = pd.read_sql_query(stmt, conn)
            frames.append(df)
            out = REPORTS / f"sql_result_{i:02d}.csv"
            out.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out, index=False)
    finally:
        conn.close()
    return frames

# -*- coding: utf-8 -*-
"""Chunked CSV load, dtype downcast, Parquet export, memory report."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from src.config import DATA_URL, MEMORY_JSON, PARQUET_PATH, RAW_CSV


def download_raw_csv(dest: Path = RAW_CSV, url: str = DATA_URL) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())
    return dest


def iter_chunks(path: Path = RAW_CSV, chunksize: int = 400) -> Iterator[pd.DataFrame]:
    for chunk in pd.read_csv(path, chunksize=chunksize):
        yield chunk


def downcast_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_integer_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], downcast="integer")
        elif pd.api.types.is_float_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], downcast="float")
    return out


def memory_mb(df: pd.DataFrame) -> float:
    return float(df.memory_usage(deep=True).sum() / (1024 ** 2))


def load_and_optimize(path: Path = RAW_CSV, chunksize: int = 400) -> tuple[pd.DataFrame, dict]:
    """Load via chunks, concatenate, downcast, write Parquet, return memory stats."""
    t0 = time.perf_counter()
    parts: list[pd.DataFrame] = []
    for chunk in iter_chunks(path, chunksize=chunksize):
        parts.append(chunk)
    raw = pd.concat(parts, ignore_index=True)
    mem_before = memory_mb(raw)
    opt = downcast_df(raw)
    mem_after = memory_mb(opt)

    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Clinical-only parquet first; enrichment overwrites later in pipeline.
    opt.to_parquet(PARQUET_PATH, index=False)
    csv_size = path.stat().st_size / (1024 ** 2)
    pq_size = PARQUET_PATH.stat().st_size / (1024 ** 2)
    elapsed = time.perf_counter() - t0

    report = {
        "rows": int(len(opt)),
        "cols": int(opt.shape[1]),
        "memory_mb_before": round(mem_before, 4),
        "memory_mb_after": round(mem_after, 4),
        "csv_mb": round(csv_size, 4),
        "parquet_mb": round(pq_size, 4),
        "load_seconds": round(elapsed, 4),
        "chunksize": chunksize,
    }
    MEMORY_JSON.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return opt, report

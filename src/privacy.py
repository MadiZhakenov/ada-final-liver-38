# -*- coding: utf-8 -*-
"""Hash patient identifiers before any DB / report / git write."""
from __future__ import annotations

import hashlib
from typing import Iterable

import pandas as pd

from src.config import get_salt


def hash_nomkart(value: str | int, salt: str | None = None) -> str:
    """Salted SHA-256 for technical case keys (Ashyq has no native NOMKART)."""
    s = salt if salt is not None else get_salt()
    payload = f"{s}|{value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def anonymize_ids(series: Iterable, salt: str | None = None) -> pd.Series:
    s = salt if salt is not None else get_salt()
    return pd.Series(series).astype(str).map(lambda x: hash_nomkart(x, s))

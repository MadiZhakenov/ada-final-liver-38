# -*- coding: utf-8 -*-
"""DEPRECATED — synthetic medical registry enrichment removed.

Instructor guidance: do not synthesize medical registry fields.
Use `src.prepare.prepare_clinical` + real egov illnesses instead.
"""
from __future__ import annotations

import warnings

import pandas as pd

from src.prepare import prepare_clinical


def enrich_registry(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    warnings.warn(
        "enrich_registry is deprecated and no longer synthesizes medical fields. "
        "Calling prepare_clinical() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _ = seed
    return prepare_clinical(df)

# -*- coding: utf-8 -*-
"""Regional rates per 100k — real egov illnesses only (no fake Ashyq regions)."""
from __future__ import annotations

import pandas as pd

from src.illnesses_kz import illnesses_rates_per_100k


def rates_per_100k(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Delegate to egov liver ICD layer. `df` kept for call-site compatibility."""
    _ = df  # clinical frame is unused — Ashyq has no real region column
    return illnesses_rates_per_100k()

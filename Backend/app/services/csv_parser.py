"""
CSV parsing and validation for Raman spectral data uploads.
Expected columns: wavenumber, intensity (case-insensitive, various aliases supported).
"""

import io
import logging
from typing import Tuple, List

import pandas as pd
import numpy as np
from fastapi import HTTPException, status

logger = logging.getLogger("spectraguard.csv_parser")

# Accepted column name aliases
WAVENUMBER_ALIASES = {"wavenumber", "wavenumbers", "raman_shift", "raman shift", "wave", "cm-1", "cm_1"}
INTENSITY_ALIASES = {"intensity", "intensities", "counts", "signal", "absorbance"}


def _find_column(df: pd.DataFrame, aliases: set) -> str:
    """Return the actual column name from df that matches any alias (case-insensitive)."""
    col_map = {c.lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias in col_map:
            return col_map[alias]
    return None


def parse_spectral_csv(
    file_bytes: bytes, filename: str
) -> Tuple[List[float], List[float]]:
    """
    Parse an uploaded CSV into (wavenumber_list, intensity_list).

    Raises HTTPException on invalid format.
    """
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot parse CSV file '{filename}': {str(exc)}",
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV file is empty",
        )

    # Locate columns
    wn_col = _find_column(df, WAVENUMBER_ALIASES)
    it_col = _find_column(df, INTENSITY_ALIASES)

    if wn_col is None or it_col is None:
        missing = []
        if wn_col is None:
            missing.append("wavenumber")
        if it_col is None:
            missing.append("intensity")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"CSV must contain columns for: {', '.join(missing)}. "
                f"Found columns: {list(df.columns)}. "
                "Accepted names: wavenumber/raman_shift/cm-1 and intensity/counts/signal."
            ),
        )

    # Coerce to numeric, drop NaN rows
    df[wn_col] = pd.to_numeric(df[wn_col], errors="coerce")
    df[it_col] = pd.to_numeric(df[it_col], errors="coerce")
    df = df.dropna(subset=[wn_col, it_col])

    if len(df) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV has only {len(df)} valid data rows after cleaning — minimum is 10.",
        )

    wavenumbers = df[wn_col].tolist()
    intensities = df[it_col].tolist()

    logger.info(f"Parsed CSV '{filename}': {len(wavenumbers)} spectral points")
    return wavenumbers, intensities

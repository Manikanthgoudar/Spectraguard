"""
CSV parsing and validation for Raman spectral data uploads.

Supports:
1. Two-column format: wavenumber, intensity (case-insensitive, aliases supported).
2. Wide Raman format: numeric wavenumber column headers (e.g. 150.0 to 3425.0) with intensity rows.
"""

import io
import logging
from typing import Tuple, List

import pandas as pd
import numpy as np
from fastapi import HTTPException, status

logger = logging.getLogger("spectraguard.csv_parser")

# Accepted column name aliases for 2-column format
WAVENUMBER_ALIASES = {"wavenumber", "wavenumbers", "raman_shift", "raman shift", "wave", "cm-1", "cm_1"}
INTENSITY_ALIASES = {"intensity", "intensities", "counts", "signal", "absorbance"}

INVALID_FORMAT_MSG = (
    "CSV must be either:\n"
    "1. two-column format: wavenumber,intensity\n"
    "or\n"
    "2. wide Raman format with numeric wavenumber columns."
)


def _find_column(df: pd.DataFrame, aliases: set) -> str:
    """Return the actual column name from df that matches any alias (case-insensitive)."""
    col_map = {str(c).lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias in col_map:
            return col_map[alias]
    return None


def parse_spectral_csv(
    file_bytes: bytes, filename: str = "uploaded_spectrum.csv"
) -> Tuple[List[float], List[float]]:
    """
    Parse an uploaded CSV into (wavenumber_list, intensity_list).

    Supports:
    - 2-column format: wavenumber, intensity
    - Wide Raman format: numeric wavenumber headers with intensity row(s)

    Raises HTTPException(422) on invalid format.
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV file is empty",
        )

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

    # Format A Check: 2-column format by column alias
    wn_col = _find_column(df, WAVENUMBER_ALIASES)
    it_col = _find_column(df, INTENSITY_ALIASES)

    if wn_col is not None and it_col is not None:
        df_sub = df[[wn_col, it_col]].copy()
        df_sub[wn_col] = pd.to_numeric(df_sub[wn_col], errors="coerce")
        df_sub[it_col] = pd.to_numeric(df_sub[it_col], errors="coerce")

        if (
            df_sub[wn_col].isna().any()
            or df_sub[it_col].isna().any()
            or np.isinf(df_sub[wn_col]).any()
            or np.isinf(df_sub[it_col]).any()
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CSV contains non-numeric, NaN, or infinite values in spectral data.",
            )

        wavenumbers = df_sub[wn_col].tolist()
        intensities = df_sub[it_col].tolist()

        if len(wavenumbers) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CSV has only {len(wavenumbers)} valid data rows after cleaning — minimum is 10.",
            )

        wn_arr = np.array(wavenumbers)
        if not np.all(np.diff(wn_arr) > 0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Wavenumbers must be in strictly ascending order.",
            )

        logger.info(f"Parsed 2-column CSV '{filename}': {len(wavenumbers)} spectral points")
        return wavenumbers, intensities

    # Drop ground truth 'label' column if present
    df_features = df.drop(columns=["label"]) if "label" in df.columns else df.copy()

    # Format A Fallback Check: 2 columns without explicit header names (numeric col 0 and col 1)
    if df_features.shape[1] == 2 and df_features.shape[0] >= 10:
        try:
            col0_num = pd.to_numeric(df_features.iloc[:, 0], errors="coerce")
            col1_num = pd.to_numeric(df_features.iloc[:, 1], errors="coerce")
            if not (
                col0_num.isna().any()
                or col1_num.isna().any()
                or np.isinf(col0_num).any()
                or np.isinf(col1_num).any()
            ):
                wn_arr = col0_num.to_numpy()
                if np.all(np.diff(wn_arr) > 0):
                    logger.info(f"Parsed 2-column CSV '{filename}': {len(wn_arr)} spectral points")
                    return col0_num.tolist(), col1_num.tolist()
        except Exception:
            pass

    # Format B Check: Wide Raman format (column headers are numeric wavenumbers)
    cols = list(df_features.columns)
    try:
        wns = np.array([float(str(c).strip()) for c in cols], dtype=np.float64)
        is_wide_header_numeric = True
    except (ValueError, TypeError):
        is_wide_header_numeric = False

    if is_wide_header_numeric and len(cols) >= 10:
        if not np.all(np.diff(wns) > 0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Wavenumber columns in wide format must be in strictly ascending order.",
            )

        first_row = df_features.iloc[0]
        intensities_series = pd.to_numeric(first_row, errors="coerce")

        if intensities_series.isna().any() or np.isinf(intensities_series.to_numpy()).any():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CSV contains non-numeric, NaN, or infinite intensity values.",
            )

        wavenumbers = wns.tolist()
        intensities = intensities_series.tolist()

        logger.info(f"Parsed wide-format CSV '{filename}': {len(wavenumbers)} spectral channels")
        return wavenumbers, intensities

    # Neither format matched -> raise format-aware error
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=INVALID_FORMAT_MSG,
    )


"""
Flexible Spectral Standardization Module - SpectraGuard ML

Provides robust resampling and alignment of raw experimental Raman spectra from
varying wavenumber ranges/resolutions onto the standard SpectraGuard 150.0–3425.0 cm⁻¹ grid.
Preserves original spectral metadata, zero-fills unmeasured regions without peak extrapolation,
and tracks missing spectral ranges.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional


STANDARD_GRID_START = 150.0
STANDARD_GRID_END = 3425.0
STANDARD_GRID_POINTS = 3276
STANDARD_GRID = np.linspace(STANDARD_GRID_START, STANDARD_GRID_END, STANDARD_GRID_POINTS)


def standardize_spectral_grid(
    wavenumbers: np.ndarray,
    intensities: np.ndarray,
    target_grid: np.ndarray = STANDARD_GRID
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Resample input Raman spectrum onto standard grid (150.0 to 3425.0 cm⁻¹, 3,276 points).

    Rules:
    1. Preserve original min/max wavenumbers and resolution.
    2. Interpolate linearly within measured range.
    3. Zero-fill unmeasured regions outside original measured range (no peak invention or extrapolation).
    4. Compute missing_range metadata string.

    Parameters:
    -----------
    wavenumbers : np.ndarray
        Original 1D wavenumber vector in ascending order.
    intensities : np.ndarray
        Original 1D intensity vector.
    target_grid : np.ndarray
        Standard target wavenumber grid (default: 3276 points from 150 to 3425 cm⁻¹).

    Returns:
    --------
    Tuple[np.ndarray, Dict[str, Any]]
        (resampled_intensities, spectral_metadata)
    """
    wn = np.asarray(wavenumbers, dtype=np.float64).flatten()
    it = np.asarray(intensities, dtype=np.float64).flatten()

    if len(wn) != len(it):
        raise ValueError(f"Wavenumber ({len(wn)}) and intensity ({len(it)}) length mismatch.")
    if len(wn) < 2:
        raise ValueError("At least 2 points required for spectral interpolation.")
    if not np.all(np.diff(wn) > 0):
        raise ValueError("Wavenumbers must be in strictly ascending order.")

    orig_min = float(wn[0])
    orig_max = float(wn[-1])
    orig_res = float(np.mean(np.diff(wn))) if len(wn) > 1 else 1.0

    # Linearly interpolate inside original measured range
    # Set left and right outside measured range to 0.0
    resampled = np.interp(target_grid, wn, it, left=0.0, right=0.0)

    # Explicitly mask unmeasured regions to 0.0
    resampled[target_grid < orig_min] = 0.0
    resampled[target_grid > orig_max] = 0.0

    # Determine missing range segments
    missing_segments = []
    if orig_min > target_grid[0]:
        missing_segments.append(f"{target_grid[0]:.1f}-{orig_min:.1f} cm⁻¹")
    if orig_max < target_grid[-1]:
        missing_segments.append(f"{orig_max:.1f}-{target_grid[-1]:.1f} cm⁻¹")

    missing_range_str = ", ".join(missing_segments) if missing_segments else "None"

    metadata = {
        "original_min_wavenumber": orig_min,
        "original_max_wavenumber": orig_max,
        "original_resolution": orig_res,
        "original_points": len(wn),
        "target_points": len(target_grid),
        "target_range": f"{target_grid[0]:.1f}–{target_grid[-1]:.1f} cm⁻¹",
        "missing_range": missing_range_str
    }

    return resampled, metadata

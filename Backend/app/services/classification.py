"""
AI Classification Engine for Raman Spectral Analysis.

Workflow:
  1. Load uploaded spectrum (wavenumber + intensity arrays)
  2. Preprocess: normalize intensities, interpolate to common grid
  3. Compute cosine similarity + Euclidean distance vs each reference
  4. Classify based on configurable thresholds
"""


import json
import logging
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from sklearn.preprocessing import normalize

from app.models.test import ClassificationResult

logger = logging.getLogger("spectraguard.classification")

# ── Classification thresholds ──────────────────────────────────────────────────
GENUINE_THRESHOLD = 0.97          # cosine similarity ≥ this → genuine
COUNTERFEIT_THRESHOLD = 0.85      # cosine similarity < this → potentially counterfeit
# Between the two → requires_verification

# Number of interpolation points for resampling spectra to a common grid
INTERP_POINTS = 512


# ── Preprocessing ──────────────────────────────────────────────────────────────

def _baseline_correction(intensity: np.ndarray) -> np.ndarray:
    """
    Simple rubber-band baseline correction:
    subtract a linear baseline drawn between the first and last points.
    """
    n = len(intensity)
    baseline = np.linspace(intensity[0], intensity[-1], n)
    corrected = intensity - baseline
    # Clip negatives to zero
    return np.clip(corrected, 0, None)


def _normalize_intensity(intensity: np.ndarray) -> np.ndarray:
    """L2-normalise the intensity vector."""
    norm = np.linalg.norm(intensity)
    if norm == 0:
        return intensity
    return intensity / norm


def _resample_spectrum(
    wavenumber: np.ndarray,
    intensity: np.ndarray,
    n_points: int = INTERP_POINTS,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resample a spectrum onto a uniform wavenumber grid via cubic interpolation.
    Returns (new_wavenumber, new_intensity).
    """
    wn_min, wn_max = wavenumber.min(), wavenumber.max()
    new_wn = np.linspace(wn_min, wn_max, n_points)
    interp_fn = interp1d(wavenumber, intensity, kind="cubic", fill_value="extrapolate")
    new_intensity = interp_fn(new_wn)
    return new_wn, new_intensity


def _smooth_spectrum(intensity: np.ndarray) -> np.ndarray:
    """Apply Savitzky-Golay smoothing (window=11, poly=3)."""
    if len(intensity) < 11:
        return intensity
    return savgol_filter(intensity, window_length=11, polyorder=3)


def preprocess_spectrum(
    wavenumber: List[float], intensity: List[float]
) -> np.ndarray:
    """
    Full preprocessing pipeline for a raw spectrum.
    Returns a normalised, smoothed, baseline-corrected intensity vector
    resampled onto a common INTERP_POINTS-point grid.
    """
    wn = np.array(wavenumber, dtype=float)
    it = np.array(intensity, dtype=float)

    # Sort by wavenumber (some uploads may be reversed)
    sort_idx = np.argsort(wn)
    wn, it = wn[sort_idx], it[sort_idx]

    # Resample
    _, it = _resample_spectrum(wn, it, INTERP_POINTS)

    # Smooth
    it = _smooth_spectrum(it)

    # Baseline correction
    it = _baseline_correction(it)

    # L2 normalise
    it = _normalize_intensity(it)

    return it


# ── Similarity metrics ─────────────────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D arrays (both should be L2-normalised)."""
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean distance between two 1-D arrays."""
    return float(np.linalg.norm(a - b))


# ── Main classification function ───────────────────────────────────────────────

def classify_spectrum(
    uploaded_wavenumber: List[float],
    uploaded_intensity: List[float],
    reference_records: List[Any],
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Compare an uploaded spectrum against all reference spectra and classify.

    Parameters
    ----------
    uploaded_wavenumber : List[float]
    uploaded_intensity  : List[float]
    reference_records   : list of ReferenceSpectrum ORM objects
    top_n               : number of top matches to return

    Returns
    -------
    dict with keys:
        classification_result, confidence_score, matched_reference_id,
        matched_drug_name, cosine_similarity, euclidean_distance,
        top_matches (list of dicts)
    """

    if not reference_records:
        logger.warning("No reference spectra available for classification")
        return {
            "classification_result": ClassificationResult.requires_verification,
            "confidence_score": 0.0,
            "matched_reference_id": None,
            "matched_drug_name": None,
            "cosine_similarity": None,
            "euclidean_distance": None,
            "top_matches": [],
        }

    # Preprocess uploaded spectrum
    uploaded_vec = preprocess_spectrum(uploaded_wavenumber, uploaded_intensity)

    scores = []
    for ref in reference_records:
        try:
            ref_wn = json.loads(ref.wavenumber_data)
            ref_it = json.loads(ref.intensity_data)
            ref_vec = preprocess_spectrum(ref_wn, ref_it)

            # Both vectors are now on INTERP_POINTS grid, safe to compare directly
            cs = cosine_similarity(uploaded_vec, ref_vec)
            ed = euclidean_distance(uploaded_vec, ref_vec)

            scores.append(
                {
                    "reference_id": ref.id,
                    "drug_name": ref.drug_name,
                    "manufacturer": ref.manufacturer,
                    "cosine_similarity": round(cs, 6),
                    "euclidean_distance": round(ed, 6),
                }
            )
        except Exception as exc:
            logger.error(f"Error processing reference ID {ref.id}: {exc}")
            continue

    if not scores:
        return {
            "classification_result": ClassificationResult.requires_verification,
            "confidence_score": 0.0,
            "matched_reference_id": None,
            "matched_drug_name": None,
            "cosine_similarity": None,
            "euclidean_distance": None,
            "top_matches": [],
        }

    # Sort by cosine similarity descending
    scores.sort(key=lambda x: x["cosine_similarity"], reverse=True)
    top_matches = scores[:top_n]
    best = scores[0]

    similarity = best["cosine_similarity"]
    confidence_score = round(similarity * 100, 2)  # as percentage

    # Classify
    if similarity >= GENUINE_THRESHOLD:
        result = ClassificationResult.genuine
    elif similarity < COUNTERFEIT_THRESHOLD:
        result = ClassificationResult.potentially_counterfeit
    else:
        result = ClassificationResult.requires_verification

    logger.info(
        f"Classification complete | result={result} | "
        f"cosine={similarity:.4f} | matched_ref={best['reference_id']}"
    )

    # Add rank to top matches
    for i, m in enumerate(top_matches, start=1):
        m["rank"] = i

    return {
        "classification_result": result,
        "confidence_score": confidence_score,
        "matched_reference_id": best["reference_id"],
        "matched_drug_name": best["drug_name"],
        "cosine_similarity": best["cosine_similarity"],
        "euclidean_distance": best["euclidean_distance"],
        "top_matches": top_matches,
    }

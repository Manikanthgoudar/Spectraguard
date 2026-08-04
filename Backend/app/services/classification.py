"""
AI Classification Engine for Raman Spectral Analysis.

Workflow:
  1. Load uploaded spectrum (wavenumber + intensity arrays)
  2. Preprocess: normalize intensities, interpolate to common grid
  3. Compute cosine similarity + Euclidean distance vs each reference
  4. Classify based on configurable thresholds
  5. Generate AI explanation + peak analysis
"""

import json
import logging
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter, find_peaks

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
    """Rubber-band baseline correction: subtract linear baseline between endpoints."""
    n = len(intensity)
    baseline = np.linspace(intensity[0], intensity[-1], n)
    corrected = intensity - baseline
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
    """Resample onto a uniform grid via cubic interpolation."""
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
    """Full preprocessing pipeline for a raw spectrum."""
    wn = np.array(wavenumber, dtype=float)
    it = np.array(intensity, dtype=float)

    sort_idx = np.argsort(wn)
    wn, it = wn[sort_idx], it[sort_idx]

    _, it = _resample_spectrum(wn, it, INTERP_POINTS)
    it = _smooth_spectrum(it)
    it = _baseline_correction(it)
    it = _normalize_intensity(it)
    return it


# ── Similarity metrics ─────────────────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


# ── Peak analysis ──────────────────────────────────────────────────────────────

def _find_spectrum_peaks(intensity: np.ndarray, wavenumbers: np.ndarray) -> List[float]:
    """
    Find significant peaks in the spectrum and return their wavenumber positions.
    Returns wavenumber values (not indices).
    """
    try:
        # Find peaks with minimum prominence to exclude noise
        prominence = max(np.std(intensity) * 0.5, 0.02)
        peak_indices, _ = find_peaks(intensity, prominence=prominence, distance=5)
        if len(peak_indices) == 0:
            return []
        peak_wns = wavenumbers[peak_indices].tolist()
        return sorted(peak_wns)
    except Exception:
        return []


def _analyze_peaks(
    uploaded_peaks: List[float],
    reference_peaks: List[float],
    tolerance: float = 15.0,
) -> Dict[str, Any]:
    """
    Compare peak positions between uploaded and reference spectra.

    Returns:
        match_count: number of matching peaks
        missing_peaks: reference peaks not found in uploaded
        extra_peaks: peaks in uploaded not in reference
        summary: human-readable summary string
    """
    if not uploaded_peaks or not reference_peaks:
        return {
            "match_count": 0,
            "missing_peaks": [],
            "extra_peaks": [],
            "summary": "Peak data insufficient for detailed comparison.",
        }

    matched_ref = set()
    matched_up = set()

    for up in uploaded_peaks:
        for i, rp in enumerate(reference_peaks):
            if abs(up - rp) <= tolerance and i not in matched_ref:
                matched_ref.add(i)
                matched_up.add(up)
                break

    match_count = len(matched_ref)
    missing = [rp for i, rp in enumerate(reference_peaks) if i not in matched_ref]
    extra = [up for up in uploaded_peaks if up not in matched_up]

    # Build summary
    parts = []
    parts.append(f"{match_count}/{len(reference_peaks)} reference peaks matched")
    if missing:
        missing_str = ", ".join([f"{m:.0f}" for m in missing[:3]])
        if len(missing) > 3:
            missing_str += f" (+{len(missing)-3} more)"
        parts.append(f"Missing peaks at: {missing_str} cm⁻¹")
    if extra:
        extra_str = ", ".join([f"{e:.0f}" for e in extra[:3]])
        if len(extra) > 3:
            extra_str += f" (+{len(extra)-3} more)"
        parts.append(f"Unexpected peaks at: {extra_str} cm⁻¹")

    summary = "; ".join(parts)
    return {
        "match_count": match_count,
        "missing_peaks": [round(p, 1) for p in missing],
        "extra_peaks": [round(p, 1) for p in extra],
        "summary": summary,
    }


# ── Risk level ─────────────────────────────────────────────────────────────────

def _compute_risk_level(result: ClassificationResult, similarity: float) -> str:
    """
    Determine risk level based on classification result and similarity score.

    Returns one of: "Low", "Medium", "High", "Critical"
    """
    if result == ClassificationResult.genuine:
        if similarity >= 0.99:
            return "Low"
        return "Low"
    elif result == ClassificationResult.requires_verification:
        if similarity >= 0.93:
            return "Medium"
        return "Medium"
    elif result == ClassificationResult.potentially_counterfeit:
        if similarity < 0.70:
            return "Critical"
        return "High"
    return "Medium"


# ── AI Explanation ─────────────────────────────────────────────────────────────

def _generate_ai_explanation(
    result: ClassificationResult,
    similarity: float,
    confidence: float,
    drug_name: str,
    matched_drug_name: Optional[str],
    peak_analysis: Dict[str, Any],
    euclidean_dist: float,
) -> str:
    """
    Generate a detailed, professional AI explanation for the classification result.
    """
    sim_pct = round(similarity * 100, 2)
    matched = matched_drug_name or drug_name
    match_count = peak_analysis.get("match_count", 0)
    missing_peaks = peak_analysis.get("missing_peaks", [])
    extra_peaks = peak_analysis.get("extra_peaks", [])

    if result == ClassificationResult.genuine:
        explanation = (
            f"The Raman spectrum of the submitted sample exhibits a cosine similarity of "
            f"{sim_pct}% against the authenticated reference spectrum for {matched}, "
            f"which exceeds the genuine classification threshold of 97.0%. "
            f"Spectral peak analysis identified {match_count} characteristic Raman peaks "
            f"in agreement with reference positions, with a Euclidean distance of "
            f"{euclidean_dist:.4f} indicating near-identical spectral fingerprint. "
        )
        if not missing_peaks:
            explanation += (
                "All expected diagnostic peaks are present at their characteristic "
                "wavenumber positions. "
            )
        explanation += (
            "The spectral profile, including peak positions, relative intensities, "
            "and band shapes, is consistent with a pharmaceutical-grade authentic product. "
            "This sample is classified as GENUINE with high confidence. "
            "No immediate regulatory action is required."
        )

    elif result == ClassificationResult.potentially_counterfeit:
        explanation = (
            f"The Raman spectrum of the submitted sample shows a cosine similarity of "
            f"{sim_pct}% against the reference spectrum for {matched}, "
            f"which falls below the minimum acceptance threshold of 85.0%. "
        )
        if missing_peaks:
            missing_str = ", ".join([f"{p:.0f} cm⁻¹" for p in missing_peaks[:4]])
            explanation += (
                f"Critical diagnostic peaks expected at {missing_str} are absent or "
                f"significantly shifted, suggesting the sample does not contain the "
                f"declared active pharmaceutical ingredient (API) at the expected purity or concentration. "
            )
        if extra_peaks:
            extra_str = ", ".join([f"{p:.0f} cm⁻¹" for p in extra_peaks[:3]])
            explanation += (
                f"Uncharacteristic spectral features detected at {extra_str} cm⁻¹ "
                f"may indicate the presence of adulterants, excipient substitutions, "
                f"or an entirely different chemical compound. "
            )
        explanation += (
            f"The Euclidean spectral distance of {euclidean_dist:.4f} confirms substantial "
            "deviation from the reference profile. This sample is classified as "
            "POTENTIALLY COUNTERFEIT. Immediate quarantine and laboratory confirmation "
            "via HPLC or mass spectrometry is strongly recommended. Report to the "
            "relevant national regulatory authority."
        )

    else:  # requires_verification
        explanation = (
            f"The Raman spectrum of the submitted sample yields a cosine similarity of "
            f"{sim_pct}% against the reference spectrum for {matched}, "
            f"placing it in the borderline verification zone (85.0%–97.0%). "
        )
        if match_count > 0:
            explanation += (
                f"While {match_count} characteristic peaks are matched, "
            )
        if missing_peaks:
            missing_str = ", ".join([f"{p:.0f} cm⁻¹" for p in missing_peaks[:3]])
            explanation += (
                f"deviations are observed at {missing_str} cm⁻¹. "
            )
        explanation += (
            "This borderline result may arise from: (1) a genuine product with "
            "manufacturing variability or different excipient composition, "
            "(2) partial degradation due to improper storage conditions, "
            "(3) a different legitimate brand or generic formulation, or "
            "(4) partial substitution of the active ingredient. "
            "This sample REQUIRES FURTHER VERIFICATION. "
            "Confirmatory analysis using HPLC, dissolution testing, or disintegration "
            "testing is recommended before release or use."
        )

    return explanation


# ── Main classification function ───────────────────────────────────────────────

def classify_spectrum(
    uploaded_wavenumber: List[float],
    uploaded_intensity: List[float],
    reference_records: List[Any],
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Compare an uploaded spectrum against all reference spectra and classify.

    Returns dict with:
        classification_result, confidence_score, matched_reference_id,
        matched_drug_name, cosine_similarity, euclidean_distance,
        risk_level, peak_match_count, peak_difference_summary,
        ai_explanation, top_matches
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
            "risk_level": "Medium",
            "peak_match_count": None,
            "peak_difference_summary": "No reference spectra available for comparison.",
            "ai_explanation": "Classification could not be performed — no reference spectra are loaded in the database.",
            "top_matches": [],
        }

    # Build interpolation grid from uploaded spectrum range
    up_wn = np.array(uploaded_wavenumber, dtype=float)
    up_it = np.array(uploaded_intensity, dtype=float)
    sort_idx = np.argsort(up_wn)
    up_wn, up_it = up_wn[sort_idx], up_it[sort_idx]

    # Preprocess uploaded spectrum
    uploaded_vec = preprocess_spectrum(uploaded_wavenumber, uploaded_intensity)

    # Reconstruct common wavenumber axis for peak finding (512-point grid)
    wn_min, wn_max = up_wn.min(), up_wn.max()
    common_wn = np.linspace(wn_min, wn_max, INTERP_POINTS)

    scores = []
    for ref in reference_records:
        try:
            ref_wn = json.loads(ref.wavenumber_data)
            ref_it = json.loads(ref.intensity_data)
            ref_vec = preprocess_spectrum(ref_wn, ref_it)

            cs = cosine_similarity(uploaded_vec, ref_vec)
            ed = euclidean_distance(uploaded_vec, ref_vec)

            scores.append(
                {
                    "reference_id": ref.id,
                    "drug_name": ref.drug_name,
                    "manufacturer": ref.manufacturer,
                    "cosine_similarity": round(cs, 6),
                    "euclidean_distance": round(ed, 6),
                    "ref_vec": ref_vec,
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
            "risk_level": "Medium",
            "peak_match_count": None,
            "peak_difference_summary": "Processing error — could not compare spectra.",
            "ai_explanation": "Classification could not be completed due to a processing error.",
            "top_matches": [],
        }

    # Sort by cosine similarity descending
    scores.sort(key=lambda x: x["cosine_similarity"], reverse=True)
    best = scores[0]

    similarity = best["cosine_similarity"]
    confidence_score = round(similarity * 100, 2)

    # Classify
    if similarity >= GENUINE_THRESHOLD:
        result = ClassificationResult.genuine
    elif similarity < COUNTERFEIT_THRESHOLD:
        result = ClassificationResult.potentially_counterfeit
    else:
        result = ClassificationResult.requires_verification

    # Peak analysis against best match
    uploaded_peaks = _find_spectrum_peaks(uploaded_vec, common_wn)
    reference_peaks = _find_spectrum_peaks(best["ref_vec"], common_wn)
    peak_analysis = _analyze_peaks(uploaded_peaks, reference_peaks)

    # Risk level
    risk_level = _compute_risk_level(result, similarity)

    # AI explanation
    ai_explanation = _generate_ai_explanation(
        result=result,
        similarity=similarity,
        confidence=confidence_score,
        drug_name=best["drug_name"],
        matched_drug_name=best["drug_name"],
        peak_analysis=peak_analysis,
        euclidean_dist=best["euclidean_distance"],
    )

    logger.info(
        f"Classification complete | result={result} | "
        f"cosine={similarity:.4f} | matched_ref={best['reference_id']} | risk={risk_level}"
    )

    # Build top_n matches (strip internal ref_vec before returning)
    top_matches = []
    for i, m in enumerate(scores[:top_n], start=1):
        top_matches.append({
            "reference_id": m["reference_id"],
            "drug_name": m["drug_name"],
            "manufacturer": m["manufacturer"],
            "cosine_similarity": m["cosine_similarity"],
            "euclidean_distance": m["euclidean_distance"],
            "rank": i,
        })

    return {
        "classification_result": result,
        "confidence_score": confidence_score,
        "matched_reference_id": best["reference_id"],
        "matched_drug_name": best["drug_name"],
        "cosine_similarity": best["cosine_similarity"],
        "euclidean_distance": best["euclidean_distance"],
        "risk_level": risk_level,
        "peak_match_count": peak_analysis["match_count"],
        "peak_difference_summary": peak_analysis["summary"],
        "ai_explanation": ai_explanation,
        "top_matches": top_matches,
    }

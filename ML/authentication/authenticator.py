"""
Raman Spectral Authenticator Engine - SpectraGuard ML

Implements reference-based spectral similarity comparison for pharmaceutical spectra.
Calculates raw Cosine Similarity scores between processed test spectra and authentic
reference standards, and evaluates decision thresholds based on statistical calibration.

Selected Similarity Algorithm: Cosine Similarity
================================================
Mathematical Definition:
    Cosine Similarity(u, v) = (u . v) / (||u||2 * ||v||2)

Calibrated Reference-Match Threshold: 0.9860
================================================
Based on statistical pairwise calibration across 150 authentic Paraguay OTC reference spectra
(3,675 within-drug pairs, 7,500 between-drug pairs), T = 0.9860 achieves 0.0% False Positive Rate
and 100% Precision for authentic reference matching.

Decision Policy Rules:
- AUTHENTIC_REFERENCE_MATCH: Cosine Similarity >= 0.9860
- UNKNOWN: Cosine Similarity < 0.9860 (Deviating/Unmatched spectrum; NOT labeled Counterfeit)
- REFERENCE_NOT_AVAILABLE: Target drug has no registered reference spectra
- INVALID_INPUT: Input spectral vector is invalid, contains NaNs/Infs, or wrong dimension
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, Tuple, Dict, Any

from .reference_manager import ReferenceManager, ReferenceRecord
from .authentication_result import ComparisonStatus, AuthenticationResult


class RamanAuthenticator:
    """
    Spectral comparison engine for pharmaceutical reference standards.
    """

    # Calibrated decision threshold derived from Step 11 statistical analysis
    DEFAULT_MATCH_THRESHOLD: float = 0.9860

    def __init__(
        self,
        reference_manager: Optional[ReferenceManager] = None,
        match_threshold: Optional[float] = None
    ):
        """
        Initialize the authenticator with a reference manager repository.
        
        Parameters:
        -----------
        reference_manager : Optional[ReferenceManager]
            Instance of ReferenceManager containing registered pharmaceutical reference records.
        match_threshold : Optional[float]
            Calibrated reference-match threshold (default=0.9860).
        """
        if reference_manager is None:
            reference_manager = ReferenceManager()
        self.reference_manager = reference_manager
        self.expected_n_features = 3276
        self.similarity_method_name = "cosine_similarity"
        self.match_threshold = match_threshold if match_threshold is not None else self.DEFAULT_MATCH_THRESHOLD

    @staticmethod
    def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate raw Cosine Similarity score between two 1D spectral vectors.
        
        Parameters:
        -----------
        vec1 : np.ndarray
            1D array of spectral intensities.
        vec2 : np.ndarray
            1D array of reference spectral intensities.
            
        Returns:
        --------
        float
            Cosine similarity score in range [0.0, 1.0].
        """
        u = np.asarray(vec1, dtype=np.float64).flatten()
        v = np.asarray(vec2, dtype=np.float64).flatten()

        if len(u) != len(v):
            raise ValueError(f"Vector length mismatch: {len(u)} vs {len(v)}")

        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)

        if norm_u == 0.0 or norm_v == 0.0:
            return 0.0

        dot_product = np.dot(u, v)
        similarity = dot_product / (norm_u * norm_v)

        # Clip numerical precision edge cases to [0.0, 1.0]
        return float(np.clip(similarity, 0.0, 1.0))

    def validate_input_spectrum(
        self,
        spectrum: Union[np.ndarray, list, pd.DataFrame, pd.Series]
    ) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        Validate input spectral vector format.
        
        Checks:
        1. Input is non-empty and non-null.
        2. Contains no NaNs or Inf values.
        3. Vector length matches expected feature count (3,276 features).
        
        Parameters:
        -----------
        spectrum : Union[np.ndarray, list, pd.DataFrame, pd.Series]
            Input spectral vector or 1-row dataframe.
            
        Returns:
        --------
        Tuple[Optional[np.ndarray], Optional[str]]
            (Validated 1D numpy vector, error_message if invalid).
        """
        if spectrum is None:
            return None, "Input spectrum is null."

        try:
            if isinstance(spectrum, pd.DataFrame):
                if spectrum.empty:
                    return None, "Input spectrum DataFrame is empty."
                # Strip label column if included
                if "label" in spectrum.columns:
                    df_feats = spectrum.drop(columns=["label"])
                else:
                    df_feats = spectrum
                vec = df_feats.iloc[0].to_numpy(dtype=np.float64)
            elif isinstance(spectrum, pd.Series):
                if "label" in spectrum.index:
                    series_feats = spectrum.drop(labels=["label"])
                else:
                    series_feats = spectrum
                vec = series_feats.to_numpy(dtype=np.float64)
            else:
                vec = np.asarray(spectrum, dtype=np.float64).flatten()
        except Exception as e:
            return None, f"Failed to convert input to numeric vector: {str(e)}"

        if vec.size == 0:
            return None, "Input spectrum vector is empty."

        if np.isnan(vec).any() or np.isinf(vec).any():
            return None, "Input spectrum contains NaN or infinite values."

        if vec.size != self.expected_n_features:
            return None, (
                f"Feature dimension error: Expected exactly {self.expected_n_features} "
                f"spectral features, but received {vec.size}."
            )

        return vec, None

    def compare_with_reference(
        self,
        target_drug_name: str,
        processed_spectrum: Union[np.ndarray, list, pd.DataFrame, pd.Series],
        reference_id: Optional[str] = None
    ) -> AuthenticationResult:
        """
        Compare a processed test spectrum against a target pharmaceutical reference spectrum.
        Evaluates decision against the calibrated threshold (0.9860).
        
        Parameters:
        -----------
        target_drug_name : str
            Name of the target drug or compound being evaluated.
        processed_spectrum : Union[np.ndarray, list, pd.DataFrame, pd.Series]
            Preprocessed spectral vector (3,276 features).
        reference_id : Optional[str]
            Optional specific reference ID to use. If None, retrieves active reference by drug name.
            
        Returns:
        --------
        AuthenticationResult
            Structured comparison result.
        """
        # Step 1: Input Validation
        vec, err_msg = self.validate_input_spectrum(processed_spectrum)
        if vec is None:
            return AuthenticationResult(
                drug_name=target_drug_name,
                similarity_score=None,
                reference_id=reference_id,
                comparison_status=ComparisonStatus.INVALID_INPUT,
                similarity_method=self.similarity_method_name,
                details={"error_message": err_msg, "threshold": self.match_threshold}
            )

        # Step 2: Retrieve Reference Spectrum
        if reference_id is not None:
            ref_record = self.reference_manager.get_reference_by_id(reference_id)
        else:
            candidate_records = self.reference_manager.get_active_references_for_drug(target_drug_name)
            if not candidate_records:
                ref_record = self.reference_manager.get_reference_by_drug(target_drug_name)
            else:
                best_ref = None
                max_sim = -1.0
                for r in candidate_records:
                    sim = self.calculate_cosine_similarity(vec, r.raman_features)
                    if sim > max_sim:
                        max_sim = sim
                        best_ref = r
                ref_record = best_ref

        if ref_record is None:
            return AuthenticationResult(
                drug_name=target_drug_name,
                similarity_score=None,
                reference_id=reference_id,
                comparison_status=ComparisonStatus.REFERENCE_NOT_AVAILABLE,
                similarity_method=self.similarity_method_name,
                details={
                    "message": f"No active reference record found for target drug '{target_drug_name}'.",
                    "threshold": self.match_threshold
                }
            )

        # Step 3: Compute Spectral Similarity Score
        similarity_score = self.calculate_cosine_similarity(vec, ref_record.raman_features)

        # Step 4: Decision Evaluation against Calibrated Threshold
        is_match = similarity_score >= self.match_threshold
        if is_match:
            status = ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
            explanation = (
                f"Spectral similarity score ({similarity_score:.6f}) meets or exceeds the "
                f"calibrated reference-match threshold ({self.match_threshold:.4f})."
            )
        else:
            status = ComparisonStatus.UNKNOWN
            explanation = (
                f"Spectral similarity score ({similarity_score:.6f}) is below the "
                f"calibrated reference-match threshold ({self.match_threshold:.4f}). "
                f"Decision is UNKNOWN (unmatched spectral profile)."
            )

        # Step 5: Construct & Return Structured Result
        return AuthenticationResult(
            drug_name=ref_record.drug_name,
            similarity_score=similarity_score,
            reference_id=ref_record.reference_id,
            comparison_status=status,
            similarity_method=self.similarity_method_name,
            details={
                "threshold": self.match_threshold,
                "is_reference_match": is_match,
                "explanation": explanation,
                "wavenumber_count": len(ref_record.wavenumbers),
                "reference_status": ref_record.reference_status,
                "source_info": ref_record.source_information
            }
        )

    def get_top_matches(
        self,
        processed_spectrum: Union[np.ndarray, list, pd.DataFrame, pd.Series],
        top_n: int = 5
    ) -> list:
        """
        Rank all registered active reference standards by cosine similarity against processed input spectrum.
        """
        vec, err_msg = self.validate_input_spectrum(processed_spectrum)
        if vec is None:
            return []

        active_refs = self.reference_manager.get_all_active_references()
        scored_matches = []
        for ref in active_refs:
            sim = self.calculate_cosine_similarity(vec, ref.raman_features)
            scored_matches.append({
                "reference_id": ref.reference_id,
                "drug_name": ref.drug_name,
                "manufacturer": ref.source_information.get("source", "Paraguay OTC Reference"),
                "brand": ref.source_information.get("brand", ""),
                "cosine_similarity": float(sim),
            })

        scored_matches.sort(key=lambda x: x["cosine_similarity"], reverse=True)

        return [
            {
                "rank": idx + 1,
                "reference_id": m["reference_id"],
                "drug_name": m["drug_name"],
                "manufacturer": m["manufacturer"],
                "brand": m["brand"],
                "cosine_similarity": m["cosine_similarity"],
            }
            for idx, m in enumerate(scored_matches[:top_n])
        ]

    def auto_identify_from_reference_library(
        self,
        processed_spectrum: Union[np.ndarray, list, pd.DataFrame, pd.Series],
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Auto-identify drug identity across the entire reference library by comparing against all active reference standards.
        
        Returns:
        --------
        Dict[str, Any] containing:
          - top_candidate_drug: str
          - max_similarity_score: float
          - top_reference_id: str
          - authentication_status: ComparisonStatus
          - is_match: bool
          - ranked_candidates: List of top_n drug matches
        """
        vec, err_msg = self.validate_input_spectrum(processed_spectrum)
        if vec is None:
            return {
                "top_candidate_drug": "Unknown",
                "max_similarity_score": None,
                "top_reference_id": None,
                "authentication_status": ComparisonStatus.INVALID_INPUT.value,
                "is_match": False,
                "threshold": self.match_threshold,
                "ranked_candidates": [],
                "error_message": err_msg
            }

        active_refs = self.reference_manager.get_all_active_references()
        if not active_refs:
            return {
                "top_candidate_drug": "Unknown",
                "max_similarity_score": None,
                "top_reference_id": None,
                "authentication_status": ComparisonStatus.REFERENCE_NOT_AVAILABLE.value,
                "is_match": False,
                "threshold": self.match_threshold,
                "ranked_candidates": [],
                "error_message": "No active reference standards registered in library."
            }

        # Group max similarity score per drug
        drug_best_scores = {}
        for ref in active_refs:
            sim = self.calculate_cosine_similarity(vec, ref.raman_features)
            dname = ref.drug_name
            if dname not in drug_best_scores or sim > drug_best_scores[dname]["similarity"]:
                drug_best_scores[dname] = {
                    "drug_name": dname,
                    "reference_id": ref.reference_id,
                    "similarity": float(sim),
                    "source": ref.source_information.get("source", "Reference Standard")
                }

        ranked = sorted(drug_best_scores.values(), key=lambda x: x["similarity"], reverse=True)
        top_match = ranked[0]
        max_sim = top_match["similarity"]
        is_match = max_sim >= self.match_threshold

        status = ComparisonStatus.AUTHENTIC_REFERENCE_MATCH.value if is_match else ComparisonStatus.UNKNOWN.value

        return {
            "top_candidate_drug": top_match["drug_name"],
            "max_similarity_score": round(float(max_sim), 6),
            "top_reference_id": top_match["reference_id"],
            "authentication_status": status,
            "is_match": is_match,
            "threshold": self.match_threshold,
            "ranked_candidates": [
                {
                    "rank": idx + 1,
                    "drug_name": c["drug_name"],
                    "reference_id": c["reference_id"],
                    "cosine_similarity": round(c["similarity"], 6),
                    "source": c["source"]
                }
                for idx, c in enumerate(ranked[:top_n])
            ]
        }



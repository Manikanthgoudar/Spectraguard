"""
Raman Analysis Service Layer - SpectraGuard Backend

Orchestrates the complete ML pipeline for incoming Raman spectral CSV data:
1. Input validation & CSV parsing (wavenumber ordering, feature count=3,276, NaN/Inf checks).
2. Spectral Preprocessing (5th-degree polynomial baseline correction + SNV normalization).
3. 32-Class Compound Classification (via pre-trained SVM model inference engine).
4. Pharmaceutical Authentication (via reference manager & calibrated authenticator T=0.9860).
5. Structured result output generation.

CRITICAL POLICY RULES:
- Calibrated authentication threshold is strictly 0.9860.
- Low similarity scores return status 'UNKNOWN' (never 'COUNTERFEIT').
- Compound classification confidence and authentication similarity score are kept separate.
- No artificial or fake counterfeit labels are generated.
"""

import os
import sys
import io
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

# Ensure project root (spectra directory) is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.csv_parser import _find_column, WAVENUMBER_ALIASES, INTENSITY_ALIASES
from ML.preprocessing.preprocess import RamanPreprocessor
from ML.training.inference import RamanInferenceEngine
from ML.authentication.reference_manager import ReferenceManager, ReferenceRecord
from ML.authentication.authenticator import RamanAuthenticator
from ML.authentication.authentication_result import ComparisonStatus

logger = logging.getLogger("spectraguard.raman_analysis_service")


class RamanAnalysisService:
    """
    Singleton / service class orchestrating compound classification and reference authentication.
    """

    EXPECTED_FEATURE_COUNT = 3276
    CALIBRATED_THRESHOLD = 0.9860

    # Naming normalization mapping for pharmaceutical reference standards
    DRUG_NAME_MAPPING = {
        "paracetamol": "Paracetamol",
        "acetaminophen": "Paracetamol",
        "para": "Paracetamol",
        "paracetamol / acetaminophen": "Paracetamol",
        "ibuprofen": "Ibuprofen",
        "ibu": "Ibuprofen",
        "acetylsalicylic acid": "Acetylsalicylic Acid",
        "acetylsalicylic-acid": "Acetylsalicylic Acid",
        "aspirin": "Acetylsalicylic Acid",
        "asa": "Acetylsalicylic Acid",
    }

    def __init__(self):
        self.preprocessor = RamanPreprocessor(poly_degree=5)
        self.inference_engine = RamanInferenceEngine()
        self.ref_manager = ReferenceManager()
        self._load_paraguay_references()
        self.authenticator = RamanAuthenticator(
            reference_manager=self.ref_manager,
            match_threshold=self.CALIBRATED_THRESHOLD
        )

    def _load_paraguay_references(self):
        """
        Load active pharmaceutical reference spectra into ReferenceManager.
        Primary Source: MySQL database reference_spectra table.
        Fallback Source: ML/authentication/references/paraguay_otc_reference.csv.
        """
        loaded_from_db = False
        try:
            from app.database import SessionLocal
            from app.models.reference_spectra import ReferenceSpectrum

            db = SessionLocal()
            try:
                db_refs = db.query(ReferenceSpectrum).filter(
                    ReferenceSpectrum.batch_reference.isnot(None),
                    ReferenceSpectrum.wavenumber_data.isnot(None),
                    ReferenceSpectrum.intensity_data.isnot(None)
                ).all()

                db_3276_refs = []
                for r in db_refs:
                    try:
                        its = json.loads(r.intensity_data)
                        if len(its) == self.EXPECTED_FEATURE_COUNT:
                            db_3276_refs.append(r)
                    except Exception:
                        pass

                if len(db_3276_refs) > 0:
                    for r in db_3276_refs:
                        wns = np.array(json.loads(r.wavenumber_data), dtype=np.float64)
                        feats = np.array(json.loads(r.intensity_data), dtype=np.float64)
                        ref_id = r.batch_reference or f"REF-DB-{r.id:03d}"
                        rec = ReferenceRecord(
                            drug_name=r.drug_name,
                            reference_id=ref_id,
                            raman_features=feats,
                            wavenumbers=wns,
                            preprocessing_metadata={"method": "5th-Degree Polynomial Baseline Subtraction + SNV Normalization"},
                            source_information={
                                "source": r.source or r.manufacturer or "",
                                "brand": r.brand_name or ""
                            },
                            reference_status="ACTIVE"
                        )
                        self.ref_manager.add_reference(rec)
                    loaded_from_db = True
                    logger.info(f"Loaded {self.ref_manager.count()} reference standards directly from MySQL database.")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not load references from MySQL database: {e}. Falling back to CSV.")

        if not loaded_from_db or self.ref_manager.count() == 0:
            self._load_csv_references()

    def _load_csv_references(self):
        """Fallback loader for CSV reference database."""
        ref_csv_path = os.path.join(
            project_root, "ML", "authentication", "references", "paraguay_otc_reference.csv"
        )
        if not os.path.exists(ref_csv_path):
            logger.error(f"Paraguay reference CSV missing at {ref_csv_path}")
            return

        try:
            df = pd.read_csv(ref_csv_path)
            feature_cols = [
                c for c in df.columns
                if c.replace('.', '', 1).isdigit() or c.endswith('.0') or ('.' in c and c.replace('.', '').isdigit())
            ]
            metadata_cols = [c for c in df.columns if c not in feature_cols]
            wavenumbers = np.array([float(c) for c in feature_cols], dtype=np.float64)

            for idx, row in df.iterrows():
                features = row[feature_cols].to_numpy(dtype=np.float64)
                ref_id = str(row["reference_id"]).strip()
                if ref_id in self.ref_manager._references_by_id:
                    continue
                rec = ReferenceRecord(
                    drug_name=row["drug_name"],
                    reference_id=ref_id,
                    raman_features=features,
                    wavenumbers=wavenumbers,
                    preprocessing_metadata={"method": row.get("preprocessing_method", "")},
                    source_information={
                        "source": row.get("source", ""),
                        "doi": row.get("doi", ""),
                        "brand": row.get("brand_or_trademark", "")
                    },
                    reference_status=row.get("reference_status", "ACTIVE")
                )
                self.ref_manager.add_reference(rec)

            logger.info(f"Loaded {self.ref_manager.count()} reference spectra from CSV repository.")
        except Exception as e:
            logger.error(f"Failed to load Paraguay reference CSV: {e}", exc_info=True)


    def get_available_drugs(self) -> list:
        """Retrieve dynamic list of active pharmaceutical drug names in reference database."""
        return self.ref_manager.get_available_drug_names()

    def normalize_drug_name(self, raw_drug_name: Optional[str]) -> Optional[str]:
        """Normalize drug name variants to official INN names or registered active reference names."""
        if not raw_drug_name or not str(raw_drug_name).strip():
            return None
        raw_str = str(raw_drug_name).strip()
        cleaned = raw_str.lower()
        if cleaned in self.DRUG_NAME_MAPPING:
            return self.DRUG_NAME_MAPPING[cleaned]

        # Case-insensitive match against registered active reference standards
        for active_name in self.ref_manager.get_available_drug_names():
            if active_name.lower() == cleaned:
                return active_name

        return raw_str


    def parse_and_validate_csv(self, csv_content: bytes) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Parse raw CSV input bytes and perform strict validation.
        
        Supports:
        1. Wide Raman format (numeric wavenumber column headers).
        2. Two-column long format (Wavenumber, Intensity).
        """
        if not csv_content or len(csv_content.strip()) == 0:
            raise ValueError("Invalid Input: Uploaded CSV file is empty.")

        try:
            df = pd.read_csv(io.BytesIO(csv_content))
        except Exception as e:
            raise ValueError(f"Invalid Input: Failed to parse CSV file: {str(e)}")

        if df.empty:
            raise ValueError("Invalid Input: CSV contains no data rows.")

        # Drop ground-truth 'label' column if present
        if "label" in df.columns:
            df_features = df.drop(columns=["label"])
        else:
            df_features = df.copy()

        # Layout Check 1: 1-row wide format (3,276 columns)
        if df_features.shape[1] == self.EXPECTED_FEATURE_COUNT:
            cols = list(df_features.columns)
            try:
                wns = np.array([float(str(c).strip()) for c in cols], dtype=np.float64)
                if not np.all(np.diff(wns) > 0):
                    raise ValueError("Invalid Input: Wavenumber headers must be in strictly ascending order.")
                wavenumbers = wns
            except ValueError as ve:
                if "strictly ascending" in str(ve):
                    raise ve
                # Fallback to standard grid if headers are non-numeric string names
                wavenumbers = np.linspace(150.0, 3425.0, self.EXPECTED_FEATURE_COUNT)

            row_vec = pd.to_numeric(df_features.iloc[0], errors="coerce").to_numpy(dtype=np.float64)

        # Layout Check 2: 2-column long format
        elif df_features.shape[1] == 2 or _find_column(df_features, WAVENUMBER_ALIASES) is not None:
            wn_col = _find_column(df_features, WAVENUMBER_ALIASES)
            it_col = _find_column(df_features, INTENSITY_ALIASES)

            if wn_col is not None and it_col is not None:
                wn_series = pd.to_numeric(df_features[wn_col], errors="coerce")
                it_series = pd.to_numeric(df_features[it_col], errors="coerce")
                is_explicit_alias = True
            elif df_features.shape[1] == 2:
                wn_series = pd.to_numeric(df_features.iloc[:, 0], errors="coerce")
                it_series = pd.to_numeric(df_features.iloc[:, 1], errors="coerce")
                is_explicit_alias = False
            else:
                wn_series = None
                is_explicit_alias = False

            if wn_series is not None:
                # If 2-column fallback without explicit alias headers has non-numeric data, raise format error
                if not is_explicit_alias and (wn_series.isna().any() or it_series.isna().any()):
                    raise ValueError(
                        "Invalid Input: CSV must be either:\n"
                        "1. two-column format: wavenumber,intensity\n"
                        "or\n"
                        "2. wide Raman format with numeric wavenumber columns."
                    )

                if len(wn_series) < 10:
                    raise ValueError("Invalid Input: CSV has insufficient spectral rows (minimum 10 required).")

                wavenumbers = wn_series.to_numpy(dtype=np.float64)
                row_vec = it_series.to_numpy(dtype=np.float64)

                if np.isnan(row_vec).any() or np.isinf(row_vec).any() or np.isnan(wavenumbers).any() or np.isinf(wavenumbers).any():
                    raise ValueError("Invalid Input: Spectral feature vector contains NaN, Null, or Infinite values.")

                if not np.all(np.diff(wavenumbers) > 0):
                    raise ValueError("Invalid Input: First column (wavenumbers) must be in strictly ascending order.")
            else:
                raise ValueError(
                    "Invalid Input: CSV must be either:\n"
                    "1. two-column format: wavenumber,intensity\n"
                    "or\n"
                    "2. wide Raman format with numeric wavenumber columns."
                )

        # Layout Check 3: Dimension error for wide format with wrong column count
        else:
            cols = list(df_features.columns)
            try:
                [float(str(c).strip()) for c in cols]
                is_numeric_cols = True
            except (ValueError, TypeError):
                is_numeric_cols = False

            if is_numeric_cols or df_features.shape[0] == 1:
                raise ValueError(
                    f"Invalid Input: Feature dimension error. Expected exactly {self.EXPECTED_FEATURE_COUNT} "
                    f"Raman spectral features, but received shape {df_features.shape}."
                )
            else:
                raise ValueError(
                    "Invalid Input: CSV must be either:\n"
                    "1. two-column format: wavenumber,intensity\n"
                    "or\n"
                    "2. wide Raman format with numeric wavenumber columns."
                )

        # Check NaN / Inf
        if np.isnan(row_vec).any() or np.isinf(row_vec).any() or np.isnan(wavenumbers).any() or np.isinf(wavenumbers).any():
            raise ValueError("Invalid Input: Spectral feature vector contains NaN, Null, or Infinite values.")

        feature_cols = [f"{wn:.1f}" for wn in wavenumbers]
        return wavenumbers, row_vec, feature_cols

    def analyze_raman_spectrum(
        self,
        csv_content: bytes,
        drug_name: Optional[str]
    ) -> Dict[str, Any]:
        """
        Full orchestration workflow:
        CSV -> Validate -> Preprocess -> SVM Classifier -> Authenticator -> Response
        """
        # Step 1: Input Validation & Parsing
        wavenumbers, raw_intensities, feature_cols = self.parse_and_validate_csv(csv_content)

        # Normalize drug name
        norm_drug_name = self.normalize_drug_name(drug_name)

        # Step 2: Spectral Preprocessing
        # Resample to 3,276 standard grid if wavenumbers differ from standard 150-3425 grid
        standard_grid = np.linspace(150.0, 3425.0, self.EXPECTED_FEATURE_COUNT)
        if len(wavenumbers) != len(standard_grid) or not np.allclose(wavenumbers, standard_grid, atol=0.5):
            resampled_intensities = np.interp(
                standard_grid, wavenumbers, raw_intensities, left=raw_intensities[0], right=0.0
            )
            # Mask high wavenumber zero padding > max measured
            resampled_intensities[standard_grid > wavenumbers.max()] = 0.0
            X_input = resampled_intensities.reshape(1, -1)
            effective_feature_cols = [f"{wn:.1f}" for wn in standard_grid]
        else:
            X_input = raw_intensities.reshape(1, -1)
            effective_feature_cols = feature_cols

        # Apply 5th degree polynomial baseline correction + SNV normalization
        preprocessed_spectrum = self.preprocessor.transform(X_input, effective_feature_cols)[0]

        # Step 3: Compound Classification (SVM Model Inference)
        inference_res = self.inference_engine.predict_sample_array(preprocessed_spectrum)
        predicted_compound = inference_res.get("predicted_compound")
        compound_confidence = inference_res.get("confidence")

        # Step 4: Pharmaceutical Reference Authentication
        if not norm_drug_name:
            auth_res = self.authenticator.compare_with_reference("Unknown", preprocessed_spectrum)
            # When drug_name is missing, status is REFERENCE_NOT_AVAILABLE
            auth_status = ComparisonStatus.REFERENCE_NOT_AVAILABLE.value
            sim_score = None
            ref_id = None
            message = "No target drug name provided for pharmaceutical reference authentication."
        else:
            auth_res = self.authenticator.compare_with_reference(norm_drug_name, preprocessed_spectrum)
            auth_status = auth_res.comparison_status.value
            sim_score = auth_res.similarity_score
            ref_id = auth_res.reference_id

            if auth_res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH:
                message = f"Matches the available authentic reference standard for {norm_drug_name}."
            elif auth_res.comparison_status == ComparisonStatus.UNKNOWN:
                message = f"Does not sufficiently match the available authentic reference standard for {norm_drug_name}."
            elif auth_res.comparison_status == ComparisonStatus.REFERENCE_NOT_AVAILABLE:
                message = f"No active reference standard is currently available for {norm_drug_name}."
            else:
                message = "Invalid input for authentication comparison."

        # Calculate Top Reference Matches from authentic Paraguay reference repository
        top_matches = self.authenticator.get_top_matches(preprocessed_spectrum, top_n=5)

        return {
            "success": True,
            "drug_name": norm_drug_name or "Unspecified",
            "predicted_compound": predicted_compound,
            "compound_confidence": round(float(compound_confidence), 4) if compound_confidence is not None else None,
            "authentication_status": auth_status,
            "similarity_score": round(float(sim_score), 6) if sim_score is not None else None,
            "authentication_threshold": self.CALIBRATED_THRESHOLD,
            "reference_id": ref_id,
            "message": message,
            "top_reference_matches": top_matches,
            "details": {
                "preprocessed_features_count": len(preprocessed_spectrum),
                "svm_model_status": inference_res.get("model_status"),
                "authentication_details": auth_res.details
            }
        }

    def auto_identify_raman_spectrum(
        self,
        csv_content: bytes
    ) -> Dict[str, Any]:
        """
        Auto-identify drug identity from uploaded Raman spectrum by searching against the entire reference library.
        """
        # Step 1: Input Validation & Parsing
        wavenumbers, raw_intensities, feature_cols = self.parse_and_validate_csv(csv_content)

        # Step 2: Spectral Preprocessing
        standard_grid = np.linspace(150.0, 3425.0, self.EXPECTED_FEATURE_COUNT)
        if len(wavenumbers) != len(standard_grid) or not np.allclose(wavenumbers, standard_grid, atol=0.5):
            resampled_intensities = np.interp(
                standard_grid, wavenumbers, raw_intensities, left=0.0, right=0.0
            )
            resampled_intensities[standard_grid > wavenumbers.max()] = 0.0
            X_input = resampled_intensities.reshape(1, -1)
            effective_feature_cols = [f"{wn:.1f}" for wn in standard_grid]
        else:
            X_input = raw_intensities.reshape(1, -1)
            effective_feature_cols = feature_cols

        preprocessed_spectrum = self.preprocessor.transform(X_input, effective_feature_cols)[0]

        # Step 3: Compound Classification (SVM Model Inference)
        inference_res = self.inference_engine.predict_sample_array(preprocessed_spectrum)
        predicted_compound = inference_res.get("predicted_compound")
        compound_confidence = inference_res.get("confidence")

        # Step 4: Reference Library Auto-Identification
        auto_res = self.authenticator.auto_identify_from_reference_library(preprocessed_spectrum, top_n=5)

        if auto_res["is_match"]:
            message = f"Identified authentic match: {auto_res['top_candidate_drug']} (Similarity: {auto_res['max_similarity_score']:.4f})"
        else:
            message = f"Top match is {auto_res['top_candidate_drug']} (Similarity: {auto_res['max_similarity_score']:.4f}), below authentication threshold {self.CALIBRATED_THRESHOLD}. Final decision: UNKNOWN."

        return {
            "success": True,
            "top_candidate_drug": auto_res["top_candidate_drug"],
            "max_similarity_score": auto_res["max_similarity_score"],
            "top_reference_id": auto_res["top_reference_id"],
            "authentication_status": auto_res["authentication_status"],
            "is_match": auto_res["is_match"],
            "authentication_threshold": self.CALIBRATED_THRESHOLD,
            "predicted_compound": predicted_compound,
            "compound_confidence": round(float(compound_confidence), 4) if compound_confidence is not None else None,
            "message": message,
            "ranked_candidates": auto_res["ranked_candidates"]
        }



# Global singleton instance
_raman_service_instance = None

def get_raman_analysis_service() -> RamanAnalysisService:
    global _raman_service_instance
    if _raman_service_instance is None:
        _raman_service_instance = RamanAnalysisService()
    return _raman_service_instance

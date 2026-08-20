"""
Safe Pharmaceutical Raman Reference Dataset Importer & Standardization Pipeline - SpectraGuard ML

Provides an extensible, reusable architecture for importing and standardizing external 
pharmaceutical Raman datasets:
1. Reads original raw spectral datasets without mutating raw files.
2. Interpolates and normalizes wavenumber grid to standard 150.0 - 3425.0 cm⁻¹ (3,276 features).
3. Applies baseline correction (5th-degree polynomial) and SNV normalization.
4. Validates every imported reference entry via ReferenceValidator.
5. Attaches mandatory provenance metadata and generates unique reference IDs.
6. Exports standardized reference CSV and produces structured import logs and validation reports.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ML.preprocessing.preprocess import RamanPreprocessor
from ML.authentication.references.validate_reference import ReferenceValidator, ValidationResult
from ML.authentication.reference_manager import ReferenceRecord, ReferenceManager


@dataclass
class ImportReport:
    """
    Structured outcome of a reference dataset import session.
    """
    dataset_name: str
    total_samples_processed: int = 0
    valid_samples_count: int = 0
    rejected_samples_count: int = 0
    imported_drugs: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "total_samples_processed": self.total_samples_processed,
            "valid_samples_count": self.valid_samples_count,
            "rejected_samples_count": self.rejected_samples_count,
            "imported_drugs": self.imported_drugs,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ReferenceDatasetImporter:
    """
    Reusable importer for pharmaceutical Raman spectroscopic reference datasets.
    """

    TARGET_START_WN = 150.0
    TARGET_END_WN = 3425.0
    TARGET_N_FEATURES = 3276

    def __init__(self, existing_reference_ids: Optional[List[str]] = None):
        """
        Initialize importer with target grid and validator instance.
        """
        self.target_wavenumbers = np.linspace(
            self.TARGET_START_WN, self.TARGET_END_WN, self.TARGET_N_FEATURES, dtype=np.float64
        )
        self.feature_cols = [f"{wn:.1f}" for wn in self.target_wavenumbers]
        self.preprocessor = RamanPreprocessor(poly_degree=5)
        self.preprocessor.fit_wavenumbers(self.feature_cols)
        self.validator = ReferenceValidator(existing_reference_ids=existing_reference_ids)

    def resample_and_standardize_grid(
        self,
        raw_wavenumbers: np.ndarray,
        raw_intensities: np.ndarray
    ) -> Tuple[np.ndarray, Optional[str]]:
        """
        Resample input spectrum onto standard SpectraGuard grid (150.0 to 3425.0 cm⁻¹, 3,276 features).
        
        Rules:
        - Linear interpolation applied within measured range.
        - High-wavenumber region above max measured wavenumber is zero-padded.
        - Rejects datasets if measured range is excessively narrow (< 800 cm⁻¹ coverage).
        """
        raw_wn = np.asarray(raw_wavenumbers, dtype=np.float64).flatten()
        raw_it = np.asarray(raw_intensities, dtype=np.float64).flatten()

        if len(raw_wn) != len(raw_it):
            return np.array([]), f"Length mismatch between raw wavenumbers ({len(raw_wn)}) and intensities ({len(raw_it)})."

        if len(raw_wn) < 10:
            return np.array([]), "Insufficient raw spectral points (minimum 10 required)."

        # Ensure ascending order
        sort_idx = np.argsort(raw_wn)
        raw_wn = raw_wn[sort_idx]
        raw_it = raw_it[sort_idx]

        min_wn = float(raw_wn[0])
        max_wn = float(raw_wn[-1])
        coverage = max_wn - min_wn

        if coverage < 800.0:
            return np.array([]), f"Spectral range too narrow ({min_wn:.1f} - {max_wn:.1f} cm⁻¹, span={coverage:.1f} cm⁻¹ < 800 cm⁻¹ required)."

        # Resample within measured range
        resampled = np.interp(
            self.target_wavenumbers,
            raw_wn,
            raw_it,
            left=raw_it[0],
            right=0.0
        )

        # Zero-pad unmeasured high wavenumber region
        resampled[self.target_wavenumbers > max_wn] = 0.0

        return resampled, None

    def preprocess_spectrum(self, resampled_intensities: np.ndarray) -> np.ndarray:
        """
        Apply 5th-degree polynomial baseline subtraction and SNV normalization.
        """
        X = resampled_intensities.reshape(1, -1)
        X_base, _ = self.preprocessor.correct_baseline(X)
        X_snv = self.preprocessor.normalize_snv(X_base)
        return X_snv.flatten()

    def process_single_reference(
        self,
        raw_wavenumbers: np.ndarray,
        raw_intensities: np.ndarray,
        metadata: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], ValidationResult]:
        """
        Process, standardize, preprocess, and validate a single candidate reference spectrum.
        """
        resampled, grid_err = self.resample_and_standardize_grid(raw_wavenumbers, raw_intensities)
        if grid_err:
            return None, ValidationResult(
                is_valid=False,
                errors=[f"Grid Standardization Error: {grid_err}"]
            )

        # Preprocess
        preprocessed_vec = self.preprocess_spectrum(resampled)

        # Validate
        val_result = self.validator.validate_reference_entry(
            features=preprocessed_vec,
            wavenumbers=self.target_wavenumbers,
            metadata=metadata
        )

        if not val_result.is_valid:
            return None, val_result

        # Construct full record dictionary
        record_dict = {**metadata}
        for col, val in zip(self.feature_cols, preprocessed_vec):
            record_dict[col] = float(val)

        return record_dict, val_result

    def import_dataset(
        self,
        dataset_name: str,
        raw_records: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, ImportReport]:
        """
        Import a batch of raw reference records.
        
        Each item in raw_records must contain:
        - 'raw_wavenumbers': 1D array
        - 'raw_intensities': 1D array
        - 'metadata': dict containing reference_id, drug_name, source, etc.
        """
        report = ImportReport(dataset_name=dataset_name)
        valid_rows = []

        for rec in raw_records:
            report.total_samples_processed += 1
            raw_wn = rec.get("raw_wavenumbers")
            raw_it = rec.get("raw_intensities")
            meta = rec.get("metadata", {})

            record_dict, val_res = self.process_single_reference(raw_wn, raw_it, meta)

            if val_res.is_valid and record_dict is not None:
                valid_rows.append(record_dict)
                report.valid_samples_count += 1
                drug = str(meta.get("drug_name", "Unknown"))
                report.imported_drugs[drug] = report.imported_drugs.get(drug, 0) + 1
                ref_id = meta.get("reference_id")
                if ref_id:
                    self.validator.existing_reference_ids.add(ref_id)
            else:
                report.rejected_samples_count += 1
                ref_id = meta.get("reference_id", f"Row-{report.total_samples_processed}")
                for err in val_res.errors:
                    report.errors.append(f"[{ref_id}] {err}")

        df_out = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
        return df_out, report

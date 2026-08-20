"""
Pharmaceutical Raman Reference Dataset Validator - SpectraGuard ML

Provides rigorous quality assurance and provenance verification for candidate
pharmaceutical reference spectra. Ensures strict compliance with feature count,
wavenumber range, numerical integrity, and mandatory source provenance.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """
    Structured outcome of reference dataset validation.
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata_summary": self.metadata_summary
        }


class ReferenceValidator:
    """
    Validation engine for pharmaceutical reference spectra and provenance metadata.
    """

    EXPECTED_FEATURE_COUNT = 3276
    EXPECTED_START_WAVENUMBER = 150.0
    EXPECTED_END_WAVENUMBER = 3425.0

    MANDATORY_METADATA_FIELDS = [
        "reference_id",
        "drug_name",
        "source"
    ]

    OPTIONAL_RECOMMENDED_FIELDS = [
        "manufacturer",
        "dosage_form",
        "collection_date",
        "spectrometer_information",
        "laser_wavelength",
        "preprocessing_method"
    ]

    def __init__(self, existing_reference_ids: Optional[List[str]] = None):
        """
        Initialize validator with optional list of existing reference IDs for duplicate detection.
        """
        self.existing_reference_ids = set(existing_reference_ids or [])

    def validate_reference_entry(
        self,
        features: Union[np.ndarray, list, pd.Series],
        wavenumbers: Union[np.ndarray, list, pd.Series],
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a single candidate reference entry.
        
        Parameters:
        -----------
        features : Union[np.ndarray, list, pd.Series]
            Intensity feature vector (3,276 numeric values).
        wavenumbers : Union[np.ndarray, list, pd.Series]
            Wavenumber positions in cm⁻¹ (3,276 numeric values).
        metadata : Dict[str, Any]
            Dictionary containing provenance and reference metadata.
            
        Returns:
        --------
        ValidationResult
            Detailed validation report containing pass/fail flag and error descriptions.
        """
        errors = []
        warnings = []
        
        # 1. Validate Metadata Presence & Mandatory Provenance Information
        if not isinstance(metadata, dict) or not metadata:
            errors.append("Validation Error: Metadata dictionary is missing or empty.")
            metadata = {}
        else:
            for req_field in self.MANDATORY_METADATA_FIELDS:
                val = metadata.get(req_field)
                if val is None or str(val).strip() == "":
                    errors.append(
                        f"Validation Error (Missing Provenance): Mandatory metadata field '{req_field}' "
                        f"is missing or empty. Reference submission rejected."
                    )

            # Check provenance / source specifically
            source_val = str(metadata.get("source", "")).strip().lower()
            if not source_val or source_val in ["unknown", "n/a", "none", "null"]:
                errors.append(
                    "Validation Error (Invalid Provenance): 'source' metadata must specify a valid, "
                    "accredited laboratory or verified institution. 'Unknown' or empty provenance is strictly prohibited."
                )

            # Duplicate reference_id check
            ref_id = str(metadata.get("reference_id", "")).strip()
            if ref_id and ref_id in self.existing_reference_ids:
                errors.append(
                    f"Validation Error (Duplicate ID): Reference ID '{ref_id}' already exists in the repository."
                )

            # Recommended metadata warnings
            for rec_field in self.OPTIONAL_RECOMMENDED_FIELDS:
                if rec_field not in metadata or not str(metadata.get(rec_field, "")).strip():
                    warnings.append(f"Recommended metadata field '{rec_field}' is missing.")

        # 2. Validate Feature Arrays Structure & Numeric Type
        try:
            feat_arr = np.asarray(features, dtype=np.float64).flatten()
        except Exception as e:
            errors.append(f"Validation Error: Failed to convert features to numeric float array: {str(e)}")
            feat_arr = np.array([])

        try:
            wave_arr = np.asarray(wavenumbers, dtype=np.float64).flatten()
        except Exception as e:
            errors.append(f"Validation Error: Failed to convert wavenumbers to numeric float array: {str(e)}")
            wave_arr = np.array([])

        # 3. Check Feature Dimensions & Alignment
        if len(feat_arr) == 0:
            errors.append("Validation Error (Feature Vector): Feature vector is empty.")
        if len(wave_arr) == 0:
            errors.append("Validation Error (Wavenumber Vector): Wavenumber array is empty.")

        if len(feat_arr) != len(wave_arr):
            errors.append(
                f"Validation Error (Dimension Mismatch): Feature count ({len(feat_arr)}) "
                f"does not match wavenumber count ({len(wave_arr)})."
            )

        # 4. Check for NaN or Inf values
        if len(feat_arr) > 0:
            if np.isnan(feat_arr).any() or np.isinf(feat_arr).any():
                errors.append("Validation Error (Invalid Values): Feature vector contains NaN, Null, or Infinite values.")

        if len(wave_arr) > 0:
            if np.isnan(wave_arr).any() or np.isinf(wave_arr).any():
                errors.append("Validation Error (Invalid Values): Wavenumber array contains NaN, Null, or Infinite values.")

        # 5. Check Wavenumber Range and Ascending Order
        if len(wave_arr) > 1 and len(feat_arr) == len(wave_arr):
            start_w = float(wave_arr[0])
            end_w = float(wave_arr[-1])
            spectral_span = end_w - start_w

            if spectral_span < 100.0:
                errors.append(
                    f"Validation Error (Insufficient Spectral Range): Total measured spectral range span "
                    f"({spectral_span:.1f} cm⁻¹) is too narrow for reliable pharmaceutical authentication."
                )

            # Check ascending order
            if not np.all(np.diff(wave_arr) > 0):
                errors.append("Validation Error (Ordering): Wavenumber values must be strictly in ascending order.")

        is_valid = (len(errors) == 0)
        
        summary = {
            "reference_id": metadata.get("reference_id"),
            "drug_name": metadata.get("drug_name"),
            "source": metadata.get("source"),
            "feature_count": len(feat_arr),
            "wavenumber_range": [float(wave_arr[0]), float(wave_arr[-1])] if len(wave_arr) > 0 else []
        }

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata_summary=summary
        )

    def validate_reference_file(self, csv_path: str, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Validate a reference spectrum from a CSV file path (supporting flexible layout formats).
        """
        if not os.path.exists(csv_path):
            return ValidationResult(
                is_valid=False,
                errors=[f"File Error: Specified CSV file does not exist at {csv_path}."]
            )

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"File Error: Failed to read CSV file: {str(e)}."]
            )

        if df.empty:
            return ValidationResult(
                is_valid=False,
                errors=["File Error: Provided CSV file is empty."]
            )

        # Flexible Format Ingestion (Wide header vs 2-column format)
        if df.shape[1] == 2:
            wavenumbers = df.iloc[:, 0].to_numpy(dtype=np.float64)
            features = df.iloc[:, 1].to_numpy(dtype=np.float64)
        elif df.shape[1] >= 10:
            try:
                wavenumbers = np.array([float(c) for c in df.columns], dtype=np.float64)
                features = df.iloc[0].to_numpy(dtype=np.float64)
            except ValueError:
                # If columns are non-numeric strings, try 2-column fallback if col names are wavenumber/intensity
                wavenumbers = df.iloc[:, 0].to_numpy(dtype=np.float64)
                features = df.iloc[:, 1].to_numpy(dtype=np.float64)
        else:
            return ValidationResult(
                is_valid=False,
                errors=["Format Error: Unsupported CSV layout. Expected wide format or 2-column format."]
            )

        return self.validate_reference_entry(features, wavenumbers, metadata)


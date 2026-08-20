"""
Unit Tests for Reference Validator Engine - SpectraGuard ML

Verifies:
1. Acceptance of valid reference entry (using a synthetic TEST VECTOR created strictly in-memory inside the test).
2. Rejection of invalid feature counts (e.g. 100 features vs expected 3,276).
3. Rejection of feature vectors containing NaN or Inf values.
4. Rejection of entries with missing provenance / source metadata.
5. Rejection of incorrect wavenumber ranges.
6. Rejection of duplicate reference IDs.

NOTE: Test vectors created here exist ONLY in transient test memory and are NEVER saved or presented as real pharmaceutical data.
"""

import unittest
import numpy as np
import pandas as pd

from ML.authentication.references.validate_reference import ReferenceValidator, ValidationResult


class TestReferenceValidator(unittest.TestCase):

    def setUp(self):
        """Set up test validator and in-memory synthetic test vector."""
        self.validator = ReferenceValidator(existing_reference_ids=["REF-EXISTING-001"])
        self.n_features = 3276
        self.valid_wavenumbers = np.linspace(150.0, 3425.0, self.n_features)
        
        # Synthetic test vector created strictly inside test memory
        np.random.seed(123)
        self.valid_test_features = np.random.uniform(5.0, 50.0, size=self.n_features)
        
        self.valid_metadata = {
            "reference_id": "REF-TEST-999",
            "drug_name": "TestDrug_INN",
            "source": "Accredited Reference Test Lab",
            "manufacturer": "USP Test Manufacturer",
            "dosage_form": "Tablet 500mg",
            "collection_date": "2026-08-10",
            "spectrometer_information": "785nm Raman Spectrometer",
            "laser_wavelength": "785nm",
            "preprocessing_method": "SNV + Baseline 5th"
        }

    def test_valid_synthetic_vector_acceptance(self):
        """Test that a fully compliant entry passes validation."""
        result = self.validator.validate_reference_entry(
            features=self.valid_test_features,
            wavenumbers=self.valid_wavenumbers,
            metadata=self.valid_metadata
        )
        self.assertTrue(result.is_valid, f"Expected valid, got errors: {result.errors}")
        self.assertEqual(len(result.errors), 0)

    def test_invalid_feature_count_rejection(self):
        """Test rejection when feature count is incorrect (e.g. 100 features)."""
        invalid_features = np.random.uniform(0, 10, 100)
        invalid_wavenumbers = np.linspace(150.0, 3425.0, 100)
        
        result = self.validator.validate_reference_entry(
            features=invalid_features,
            wavenumbers=invalid_wavenumbers,
            metadata=self.valid_metadata
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Feature Count" in err for err in result.errors))

    def test_nan_values_rejection(self):
        """Test rejection when features contain NaN or Inf values."""
        features_with_nan = self.valid_test_features.copy()
        features_with_nan[50] = np.nan
        
        result = self.validator.validate_reference_entry(
            features=features_with_nan,
            wavenumbers=self.valid_wavenumbers,
            metadata=self.valid_metadata
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Invalid Values" in err for err in result.errors))

    def test_missing_provenance_source_rejection(self):
        """Test strict rejection when mandatory provenance / source metadata is missing or 'Unknown'."""
        # Case A: Missing source field
        meta_no_source = self.valid_metadata.copy()
        del meta_no_source["source"]
        res_no_source = self.validator.validate_reference_entry(
            features=self.valid_test_features,
            wavenumbers=self.valid_wavenumbers,
            metadata=meta_no_source
        )
        self.assertFalse(res_no_source.is_valid)
        self.assertTrue(any("Missing Provenance" in err for err in res_no_source.errors))

        # Case B: 'Unknown' source field
        meta_unknown_source = self.valid_metadata.copy()
        meta_unknown_source["source"] = "Unknown"
        res_unknown = self.validator.validate_reference_entry(
            features=self.valid_test_features,
            wavenumbers=self.valid_wavenumbers,
            metadata=meta_unknown_source
        )
        self.assertFalse(res_unknown.is_valid)
        self.assertTrue(any("Invalid Provenance" in err for err in res_unknown.errors))

    def test_incorrect_wavenumber_range_rejection(self):
        """Test rejection when wavenumber range does not match 150.0 to 3425.0 cm⁻¹."""
        wrong_wavenumbers = np.linspace(200.0, 3000.0, self.n_features)
        result = self.validator.validate_reference_entry(
            features=self.valid_test_features,
            wavenumbers=wrong_wavenumbers,
            metadata=self.valid_metadata
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Wavenumber Range" in err for err in result.errors))

    def test_duplicate_reference_id_rejection(self):
        """Test rejection when reference_id already exists in repository."""
        duplicate_meta = self.valid_metadata.copy()
        duplicate_meta["reference_id"] = "REF-EXISTING-001"
        
        result = self.validator.validate_reference_entry(
            features=self.valid_test_features,
            wavenumbers=self.valid_wavenumbers,
            metadata=duplicate_meta
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Duplicate ID" in err for err in result.errors))


if __name__ == "__main__":
    unittest.main()

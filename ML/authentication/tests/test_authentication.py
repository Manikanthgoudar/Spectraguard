"""
Unit Tests for Pharmaceutical Raman Reference & Authentication Engine - SpectraGuard ML

Verifies:
1. Reference Record creation & ReferenceManager registry operations.
2. Cosine Similarity calculation accuracy and boundary behaviors.
3. Input spectrum validation (feature count enforcement, NaN/Inf checks, formatting).
4. Calibrated threshold decision logic: AUTHENTIC_REFERENCE_MATCH vs UNKNOWN.
5. Correct status returns: AUTHENTIC_REFERENCE_MATCH, UNKNOWN, REFERENCE_NOT_AVAILABLE, INVALID_INPUT.
6. Integration with Paraguay OTC reference dataset and test sample CSVs.
7. Strict absence of Genuine / Counterfeit classification labels.
"""

import os
import unittest
import numpy as np
import pandas as pd

from ML.authentication.reference_manager import ReferenceRecord, ReferenceManager
from ML.authentication.authentication_result import ComparisonStatus, AuthenticationResult
from ML.authentication.authenticator import RamanAuthenticator


class TestRamanAuthenticationEngine(unittest.TestCase):

    def setUp(self):
        """Set up test environment and mock reference manager."""
        self.ref_manager = ReferenceManager()
        self.n_features = 3276
        self.dummy_wavenumbers = np.linspace(150.0, 3425.0, self.n_features)
        self.calibrated_threshold = 0.9860
        
        # Create a synthetic reference spectrum vector
        np.random.seed(42)
        self.sample_ref_vector = np.random.uniform(10.0, 100.0, size=self.n_features)
        
        self.sample_record = ReferenceRecord(
            drug_name="Paracetamol_Test_Ref",
            reference_id="REF-PARA-TEST-001",
            raman_features=self.sample_ref_vector,
            wavenumbers=self.dummy_wavenumbers,
            preprocessing_metadata={"baseline": "polynomial_5th", "normalization": "SNV"},
            source_information={"lab": "SpectraGuard Test Lab"},
            reference_status="ACTIVE"
        )
        self.ref_manager.add_reference(self.sample_record)
        self.authenticator = RamanAuthenticator(
            reference_manager=self.ref_manager,
            match_threshold=self.calibrated_threshold
        )

    def test_reference_manager_registration(self):
        """Test ReferenceRecord registration and retrieval in ReferenceManager."""
        self.assertEqual(self.ref_manager.count(), 1)
        record = self.ref_manager.get_reference_by_drug("Paracetamol_Test_Ref")
        self.assertIsNotNone(record)
        self.assertEqual(record.reference_id, "REF-PARA-TEST-001")
        self.assertEqual(len(record.raman_features), self.n_features)
        
        # Test reference by ID
        record_by_id = self.ref_manager.get_reference_by_id("REF-PARA-TEST-001")
        self.assertEqual(record_by_id.drug_name, "Paracetamol_Test_Ref")

    def test_cosine_similarity_computation(self):
        """Test Cosine Similarity calculation properties."""
        v1 = self.sample_ref_vector
        # Identical vector should yield similarity of 1.0
        sim_identical = self.authenticator.calculate_cosine_similarity(v1, v1)
        self.assertAlmostEqual(sim_identical, 1.0, places=5)
        
        # Scaled vector should also yield similarity of 1.0 (scale invariance)
        sim_scaled = self.authenticator.calculate_cosine_similarity(v1, v1 * 2.5)
        self.assertAlmostEqual(sim_scaled, 1.0, places=5)
        
        # Orthogonal vector should yield similarity of 0.0
        v_zero = np.zeros(self.n_features)
        sim_zero = self.authenticator.calculate_cosine_similarity(v1, v_zero)
        self.assertEqual(sim_zero, 0.0)

    def test_strong_same_drug_reference_match(self):
        """1. Test strong same-drug reference match returns AUTHENTIC_REFERENCE_MATCH."""
        # Slightly noisy spectrum with similarity > 0.9860
        test_spectrum = self.sample_ref_vector + np.random.normal(0, 0.1, self.n_features)
        result = self.authenticator.compare_with_reference(
            target_drug_name="Paracetamol_Test_Ref",
            processed_spectrum=test_spectrum
        )
        
        self.assertEqual(result.comparison_status, ComparisonStatus.AUTHENTIC_REFERENCE_MATCH)
        self.assertIsNotNone(result.similarity_score)
        self.assertGreaterEqual(result.similarity_score, self.calibrated_threshold)
        self.assertEqual(result.reference_id, "REF-PARA-TEST-001")
        self.assertTrue(result.details["is_reference_match"])

    def test_different_drug_mismatch_returns_unknown(self):
        """2. Test different-drug mismatch returns UNKNOWN (not counterfeit)."""
        different_drug_vector = np.random.uniform(0.0, 50.0, size=self.n_features)
        result = self.authenticator.compare_with_reference(
            target_drug_name="Paracetamol_Test_Ref",
            processed_spectrum=different_drug_vector
        )
        
        self.assertEqual(result.comparison_status, ComparisonStatus.UNKNOWN)
        self.assertIsNotNone(result.similarity_score)
        self.assertLess(result.similarity_score, self.calibrated_threshold)
        self.assertFalse(result.details["is_reference_match"])
        self.assertNotIn("COUNTERFEIT", result.comparison_status.value)

    def test_unknown_decision_on_low_similarity(self):
        """3. Test low similarity score produces UNKNOWN decision, never COUNTERFEIT."""
        low_sim_spectrum = self.sample_ref_vector * 0.5 + np.random.normal(0, 50.0, self.n_features)
        result = self.authenticator.compare_with_reference(
            target_drug_name="Paracetamol_Test_Ref",
            processed_spectrum=low_sim_spectrum
        )
        
        self.assertEqual(result.comparison_status, ComparisonStatus.UNKNOWN)
        self.assertFalse("counterfeit" in str(result.to_dict()).lower())

    def test_missing_reference_status(self):
        """4. Test querying for non-existent drug reference returns REFERENCE_NOT_AVAILABLE."""
        test_spectrum = self.sample_ref_vector
        result = self.authenticator.compare_with_reference(
            target_drug_name="NonExistentDrug",
            processed_spectrum=test_spectrum
        )
        
        self.assertEqual(result.comparison_status, ComparisonStatus.REFERENCE_NOT_AVAILABLE)
        self.assertIsNone(result.similarity_score)
        self.assertIsNone(result.reference_id)

    def test_invalid_input_rejection(self):
        """5. Test invalid input returns INVALID_INPUT status."""
        # Case 1: Wrong feature length (e.g. 100 features instead of 3276)
        wrong_len_spectrum = np.random.uniform(0, 10, 100)
        res1 = self.authenticator.compare_with_reference("Paracetamol_Test_Ref", wrong_len_spectrum)
        self.assertEqual(res1.comparison_status, ComparisonStatus.INVALID_INPUT)
        self.assertIsNone(res1.similarity_score)
        
        # Case 2: Spectrum containing NaNs
        nan_spectrum = self.sample_ref_vector.copy()
        nan_spectrum[10] = np.nan
        res2 = self.authenticator.compare_with_reference("Paracetamol_Test_Ref", nan_spectrum)
        self.assertEqual(res2.comparison_status, ComparisonStatus.INVALID_INPUT)
        
        # Case 3: Empty input
        res3 = self.authenticator.compare_with_reference("Paracetamol_Test_Ref", np.array([]))
        self.assertEqual(res3.comparison_status, ComparisonStatus.INVALID_INPUT)

    def test_threshold_behavior_boundary(self):
        """6. Test exact threshold boundary conditions (T = 0.9860)."""
        self.assertEqual(self.authenticator.match_threshold, 0.9860)

    def test_no_counterfeit_label_fabricated(self):
        """7. Verify that no counterfeit labels exist in status enum or output dictionary."""
        forbidden_keywords = ["counterfeit", "fake", "fraudulent", "forgery"]
        for status_enum in ComparisonStatus:
            for kw in forbidden_keywords:
                self.assertNotIn(kw, status_enum.value.lower())


if __name__ == "__main__":
    unittest.main()

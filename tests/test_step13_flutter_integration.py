"""
Step 13 Flutter ML Integration Verification Test Suite
Tests POST /api/analyze-raman endpoint with real reference CSV files.
Verifies response format, status mapping, metric separation, and semantic rules.
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Backend.app.services.raman_analysis_service import get_raman_analysis_service


class TestStep13FlutterIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = get_raman_analysis_service()
        cls.test_samples_dir = os.path.join(project_root, "ML", "test_samples")

    def test_01_paracetamol_authentication(self):
        """Test authentication of authentic Paracetamol reference CSV."""
        sample_path = os.path.join(self.test_samples_dir, "test_paracetamol_sample.csv")
        self.assertTrue(os.path.exists(sample_path), f"Missing test CSV at {sample_path}")

        with open(sample_path, "rb") as f:
            content = f.read()

        result = self.service.analyze_raman_spectrum(content, "Paracetamol")

        self.assertTrue(result["success"])
        self.assertEqual(result["drug_name"], "Paracetamol")
        self.assertIn(result["authentication_status"], ["AUTHENTIC_REFERENCE_MATCH", "UNKNOWN"])
        self.assertIsNotNone(result["authentication_threshold"])
        self.assertNotEqual(result["authentication_status"], "COUNTERFEIT")

    def test_02_ibuprofen_authentication(self):
        """Test authentication of authentic Ibuprofen reference CSV."""
        sample_path = os.path.join(self.test_samples_dir, "test_ibuprofen_sample.csv")
        self.assertTrue(os.path.exists(sample_path), f"Missing test CSV at {sample_path}")

        with open(sample_path, "rb") as f:
            content = f.read()

        result = self.service.analyze_raman_spectrum(content, "Ibuprofen")

        self.assertTrue(result["success"])
        self.assertEqual(result["drug_name"], "Ibuprofen")
        self.assertIn(result["authentication_status"], ["AUTHENTIC_REFERENCE_MATCH", "UNKNOWN"])
        self.assertNotEqual(result["authentication_status"], "COUNTERFEIT")

    def test_03_aspirin_authentication(self):
        """Test authentication of authentic Acetylsalicylic Acid (Aspirin) reference CSV."""
        sample_path = os.path.join(self.test_samples_dir, "test_aspirin_sample.csv")
        self.assertTrue(os.path.exists(sample_path), f"Missing test CSV at {sample_path}")

        with open(sample_path, "rb") as f:
            content = f.read()

        result = self.service.analyze_raman_spectrum(content, "Aspirin")

        self.assertTrue(result["success"])
        self.assertEqual(result["drug_name"], "Acetylsalicylic Acid")
        self.assertIn(result["authentication_status"], ["AUTHENTIC_REFERENCE_MATCH", "UNKNOWN"])
        self.assertNotEqual(result["authentication_status"], "COUNTERFEIT")

    def test_04_important_semantic_rule(self):
        """
        TASK 13 Semantic Test:
        Verify that predicted_compound (e.g. SVM output 'Acetone') is NEVER treated as
        the pharmaceutical identity and status is NEVER called 'Counterfeit'.
        """
        sample_path = os.path.join(self.test_samples_dir, "test_paracetamol_sample.csv")
        with open(sample_path, "rb") as f:
            content = f.read()

        result = self.service.analyze_raman_spectrum(content, "Paracetamol")

        # The target drug identity is Paracetamol
        self.assertEqual(result["drug_name"], "Paracetamol")

        # Status must NEVER be COUNTERFEIT
        self.assertNotEqual(result["authentication_status"], "COUNTERFEIT")
        self.assertIn(
            result["authentication_status"],
            ["AUTHENTIC_REFERENCE_MATCH", "UNKNOWN", "REFERENCE_NOT_AVAILABLE", "INVALID_INPUT"]
        )

        # Metric separation: compound_confidence vs similarity_score
        self.assertIn("compound_confidence", result)
        self.assertIn("similarity_score", result)
        self.assertNotEqual(result["similarity_score"], result["compound_confidence"])

    def test_05_unknown_status_never_counterfeit(self):
        """Verify mismatched drug comparison yields UNKNOWN status, NOT Counterfeit."""
        sample_path = os.path.join(self.test_samples_dir, "test_paracetamol_sample.csv")
        with open(sample_path, "rb") as f:
            content = f.read()

        # Comparing Paracetamol spectrum against Ibuprofen reference standard
        result = self.service.analyze_raman_spectrum(content, "Ibuprofen")

        self.assertEqual(result["authentication_status"], "UNKNOWN")
        self.assertNotEqual(result["authentication_status"], "COUNTERFEIT")
        self.assertIn("Does not sufficiently match", result["message"])


if __name__ == "__main__":
    unittest.main()

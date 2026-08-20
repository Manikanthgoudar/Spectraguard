"""
Backend FastAPI Integration Tests for Raman Analysis & Pharmaceutical Authentication API - SpectraGuard ML

Tests:
1. Valid Paracetamol Raman CSV input -> AUTHENTIC_REFERENCE_MATCH
2. Valid Ibuprofen Raman CSV input -> AUTHENTIC_REFERENCE_MATCH
3. Valid Aspirin / Acetylsalicylic Acid Raman CSV input -> AUTHENTIC_REFERENCE_MATCH
4. Missing drug_name -> REFERENCE_NOT_AVAILABLE
5. Unsupported drug (e.g., Amoxicillin) -> REFERENCE_NOT_AVAILABLE
6. Invalid CSV -> HTTP 400 Bad Request
7. Incorrect feature count (100 columns instead of 3276) -> HTTP 400 Bad Request
8. Spectrum with NaN/Inf values -> HTTP 400 Bad Request
9. Authentication match status (similarity >= 0.9860) -> AUTHENTIC_REFERENCE_MATCH
10. Authentication UNKNOWN status (similarity < 0.9860) -> UNKNOWN (Never COUNTERFEIT)
11. Reference unavailable status -> REFERENCE_NOT_AVAILABLE
12. Existing backend endpoints (/health, /, /docs) remain functional
"""

import os
import sys
import io
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "Backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from Backend.app.main import app

class TestRamanAnalysisBackendAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up FastAPI TestClient and load real Paraguay reference dataset for test CSV creation."""
        cls.client = TestClient(app)
        cls.ref_csv_path = os.path.join(project_root, "ML", "authentication", "references", "paraguay_otc_reference.csv")
        cls.assertTrue(os.path.exists(cls.ref_csv_path), f"Reference CSV missing at {cls.ref_csv_path}")
        
        cls.df_ref = pd.read_csv(cls.ref_csv_path)
        cls.feature_cols = [
            c for c in cls.df_ref.columns
            if c.replace('.', '', 1).isdigit() or c.endswith('.0') or ('.' in c and c.replace('.', '').isdigit())
        ]
        assert len(cls.feature_cols) == 3276, f"Expected 3276 features, got {len(cls.feature_cols)}"

    def _create_csv_bytes(self, row_idx: int) -> bytes:
        """Helper to create a 1-row valid CSV byte stream from Paraguay reference data."""
        row_features = self.df_ref.iloc[row_idx][self.feature_cols].to_dict()
        df_single = pd.DataFrame([row_features])
        out_buf = io.BytesIO()
        df_single.to_csv(out_buf, index=False)
        return out_buf.getvalue()

    def test_01_valid_paracetamol_input(self):
        """1. Valid Paracetamol Raman input returns 200 and AUTHENTIC_REFERENCE_MATCH."""
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[0]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("paracetamol_test.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["drug_name"], "Paracetamol")
        self.assertEqual(data["authentication_status"], "AUTHENTIC_REFERENCE_MATCH")
        self.assertIsNotNone(data["similarity_score"])
        self.assertGreaterEqual(data["similarity_score"], 0.9860)
        self.assertEqual(data["authentication_threshold"], 0.9860)
        self.assertIsNotNone(data["predicted_compound"])
        self.assertIsNotNone(data["compound_confidence"])
        self.assertIn("Matches the available authentic reference", data["message"])

    def test_02_valid_ibuprofen_input(self):
        """2. Valid Ibuprofen Raman input returns 200 and AUTHENTIC_REFERENCE_MATCH."""
        ibu_idx = self.df_ref[self.df_ref["drug_name"] == "Ibuprofen"].index[-1]
        csv_bytes = self._create_csv_bytes(ibu_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("ibuprofen_test.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Ibuprofen"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["drug_name"], "Ibuprofen")
        self.assertEqual(data["authentication_status"], "AUTHENTIC_REFERENCE_MATCH")
        self.assertGreaterEqual(data["similarity_score"], 0.9860)

    def test_03_valid_aspirin_input(self):
        """3. Valid Aspirin/Acetylsalicylic Acid input returns 200 and AUTHENTIC_REFERENCE_MATCH."""
        asa_idx = self.df_ref[self.df_ref["drug_name"] == "Acetylsalicylic Acid"].index[0]
        csv_bytes = self._create_csv_bytes(asa_idx)

        # Test name alias "Aspirin"
        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("aspirin_test.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Aspirin"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["drug_name"], "Acetylsalicylic Acid")
        self.assertEqual(data["authentication_status"], "AUTHENTIC_REFERENCE_MATCH")
        self.assertGreaterEqual(data["similarity_score"], 0.9860)

    def test_04_missing_drug_name(self):
        """4. Missing drug_name returns REFERENCE_NOT_AVAILABLE for authentication."""
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[0]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test.csv", csv_bytes, "text/csv")}
            # drug_name not sent
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["authentication_status"], "REFERENCE_NOT_AVAILABLE")
        self.assertIsNone(data["similarity_score"])
        self.assertIsNotNone(data["predicted_compound"])

    def test_05_unsupported_drug_name(self):
        """5. Unsupported drug (e.g. Amoxicillin) returns REFERENCE_NOT_AVAILABLE."""
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[0]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Amoxicillin"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["drug_name"], "Amoxicillin")
        self.assertEqual(data["authentication_status"], "REFERENCE_NOT_AVAILABLE")
        self.assertIsNone(data["similarity_score"])

    def test_06_invalid_csv_format(self):
        """6. Invalid CSV (corrupted text) returns HTTP 400 Bad Request."""
        corrupted_bytes = b"This is not a CSV content, corrupted payload $$$#"

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("corrupted.csv", corrupted_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_07_incorrect_feature_count(self):
        """7. Incorrect feature count (100 columns) returns HTTP 400 Bad Request."""
        short_df = pd.DataFrame([np.random.uniform(0, 10, 100)])
        out_buf = io.BytesIO()
        short_df.to_csv(out_buf, index=False)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("short.csv", out_buf.getvalue(), "text/csv")},
            data={"drug_name": "Paracetamol"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Feature dimension error", response.json()["detail"])

    def test_08_nan_inf_values(self):
        """8. Spectrum containing NaNs returns HTTP 400 Bad Request."""
        row_dict = self.df_ref.iloc[0][self.feature_cols].to_dict()
        row_dict[self.feature_cols[10]] = np.nan
        nan_df = pd.DataFrame([row_dict])
        out_buf = io.BytesIO()
        nan_df.to_csv(out_buf, index=False)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("nan.csv", out_buf.getvalue(), "text/csv")},
            data={"drug_name": "Paracetamol"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("NaN", response.json()["detail"])

    def test_09_authentication_match_status(self):
        """9. Authentication match status returns AUTHENTIC_REFERENCE_MATCH."""
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[1]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("para_match.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )

        data = response.json()
        self.assertEqual(data["authentication_status"], "AUTHENTIC_REFERENCE_MATCH")
        self.assertGreaterEqual(data["similarity_score"], 0.9860)

    def test_10_authentication_unknown_status(self):
        """10. Cross-drug spectrum returns UNKNOWN status (never COUNTERFEIT)."""
        # Pass Paracetamol spectrum but specify target drug "Ibuprofen"
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[0]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("para_as_ibu.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Ibuprofen"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["authentication_status"], "UNKNOWN")
        self.assertLess(data["similarity_score"], 0.9860)
        self.assertIn("Does not sufficiently match", data["message"])
        self.assertNotIn("counterfeit", data["message"].lower())
        self.assertNotIn("counterfeit", data["authentication_status"].lower())

    def test_11_reference_unavailable_status(self):
        """11. Querying unsupported drug returns REFERENCE_NOT_AVAILABLE."""
        para_idx = self.df_ref[self.df_ref["drug_name"] == "Paracetamol"].index[0]
        csv_bytes = self._create_csv_bytes(para_idx)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Ciprofloxacin"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["authentication_status"], "REFERENCE_NOT_AVAILABLE")
        self.assertIsNone(data["similarity_score"])

    def test_12_existing_backend_endpoints(self):
        """12. Existing backend endpoints (/health, /, /docs) remain functional."""
        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "ok")

        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertIn("SpectraGuard API", res_root.json()["message"])

        res_docs = self.client.get("/docs")
        self.assertEqual(res_docs.status_code, 200)


if __name__ == "__main__":
    unittest.main()

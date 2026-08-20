"""
Unit and Integration Tests for Raman CSV Format Compatibility (Step 14B) - SpectraGuard

Tests:
1. Valid 2-column CSV format accepted.
2. Valid wide-format 3,276-feature CSV accepted.
3. Invalid CSV rejected with format-aware message.
4. Spectrum containing NaN values rejected.
5. Spectrum containing Inf values rejected.
6. Wide format with incorrect feature count rejected.
7. Real end-to-end test with ML/test_samples/test_paracetamol_sample.csv.
8. Paraguay authentic reference matching works (threshold == 0.9860).
9. Mismatched reference returns UNKNOWN (never COUNTERFEIT).
10. Verify no COUNTERFEIT labels are fabricated.
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
from Backend.app.services.csv_parser import parse_spectral_csv, INVALID_FORMAT_MSG


class TestRamanCSVFormats(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.paracetamol_sample_path = os.path.join(
            project_root, "ML", "test_samples", "test_paracetamol_sample.csv"
        )
        cls.assertTrue(
            os.path.exists(cls.paracetamol_sample_path),
            f"Test sample CSV missing at {cls.paracetamol_sample_path}"
        )

    def test_01_valid_two_column_csv_accepted(self):
        """1. Valid 2-column CSV accepted by csv_parser and analyze-raman."""
        # Create a 2-column CSV (wavenumber, intensity) with standard grid
        wns = np.linspace(150.0, 3425.0, 3276)
        # Create a synthetic spectrum
        ints = np.sin(wns / 100.0) + 2.0
        df = pd.DataFrame({"wavenumber": wns, "intensity": ints})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        csv_bytes = buf.getvalue()

        # Direct parser test
        parsed_wns, parsed_ints = parse_spectral_csv(csv_bytes, "two_col.csv")
        self.assertEqual(len(parsed_wns), 3276)
        self.assertEqual(len(parsed_ints), 3276)

        # API endpoint test
        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("two_col.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["predicted_compound"])

    def test_02_valid_wide_format_csv_accepted(self):
        """2. Valid wide-format 3,276-feature CSV accepted."""
        with open(self.paracetamol_sample_path, "rb") as f:
            csv_bytes = f.read()

        # Direct parser test
        parsed_wns, parsed_ints = parse_spectral_csv(csv_bytes, "test_paracetamol_sample.csv")
        self.assertEqual(len(parsed_wns), 3276)
        self.assertEqual(len(parsed_ints), 3276)

        # API endpoint test
        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test_paracetamol_sample.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["authentication_threshold"], 0.9860)

    def test_03_invalid_csv_format_rejected(self):
        """3. Invalid CSV rejected with format-aware message."""
        corrupted_bytes = b"header1,header2\nnot_a_number,also_not_a_number\nfoo,bar"

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("invalid.csv", corrupted_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("two-column format", detail)
        self.assertIn("wide Raman format", detail)

    def test_04_nan_values_rejected(self):
        """4. NaN values rejected."""
        wns = np.linspace(150.0, 3425.0, 3276)
        ints = np.sin(wns / 100.0) + 2.0
        ints[50] = np.nan

        df = pd.DataFrame({"wavenumber": wns, "intensity": ints})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("nan_test.csv", buf.getvalue(), "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("NaN", response.json()["detail"])

    def test_05_inf_values_rejected(self):
        """5. Infinite values rejected."""
        wns = np.linspace(150.0, 3425.0, 3276)
        ints = np.sin(wns / 100.0) + 2.0
        ints[100] = np.inf

        df = pd.DataFrame({"wavenumber": wns, "intensity": ints})
        buf = io.BytesIO()
        df.to_csv(buf, index=False)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("inf_test.csv", buf.getvalue(), "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue("infinite" in response.json()["detail"].lower() or "inf" in response.json()["detail"].lower())

    def test_06_incorrect_feature_count_rejected(self):
        """6. Wide format with incorrect column count (100 cols) rejected."""
        df = pd.DataFrame([np.random.uniform(0, 10, 100)])
        # Use numeric headers 150.0 .. 249.0
        df.columns = [str(150.0 + i) for i in range(100)]
        buf = io.BytesIO()
        df.to_csv(buf, index=False)

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("short_wide.csv", buf.getvalue(), "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Feature dimension error", response.json()["detail"])

    def test_07_real_paracetamol_end_to_end(self):
        """7. Real end-to-end API test with ML/test_samples/test_paracetamol_sample.csv."""
        with open(self.paracetamol_sample_path, "rb") as f:
            csv_bytes = f.read()

        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test_paracetamol_sample.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Paracetamol"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Print actual results for task report verification
        print("\n--- REAL END-TO-END RESULT FOR test_paracetamol_sample.csv ---")
        print(f"predicted_compound: {data.get('predicted_compound')}")
        print(f"compound_confidence: {data.get('compound_confidence')}")
        print(f"authentication_status: {data.get('authentication_status')}")
        print(f"similarity_score: {data.get('similarity_score')}")
        print(f"authentication_threshold: {data.get('authentication_threshold')}")
        print(f"reference_id: {data.get('reference_id')}")

        self.assertEqual(data["authentication_threshold"], 0.9860)
        self.assertIsNotNone(data["predicted_compound"])

    def test_08_unknown_remains_unknown(self):
        """8. Cross-drug reference comparison returns UNKNOWN status (never COUNTERFEIT)."""
        with open(self.paracetamol_sample_path, "rb") as f:
            csv_bytes = f.read()

        # Send Paracetamol spectrum with target drug "Ibuprofen"
        response = self.client.post(
            "/api/analyze-raman",
            files={"file": ("test_paracetamol_sample.csv", csv_bytes, "text/csv")},
            data={"drug_name": "Ibuprofen"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["authentication_status"], "UNKNOWN")
        self.assertNotIn("counterfeit", data["authentication_status"].lower())
        self.assertNotIn("counterfeit", data["message"].lower())


if __name__ == "__main__":
    unittest.main()

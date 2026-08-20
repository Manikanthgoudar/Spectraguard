"""
Step 15 Test Suite — SpectraGuard Pharmaceutical Reference Expansion Architecture

Validates reference discoverability, dynamic drug listing API, reference import support,
strict input validation (dimension, NaN/Inf, duplicate ID, missing provenance),
and preservation of authentication threshold (0.9860), UNKNOWN decision status, and non-counterfeit labeling.
"""

import os
import sys

# Override database URL to SQLite for testing
os.environ["DATABASE_URL_OVERRIDE"] = "sqlite:///./test_spectraguard.db"
os.environ["DATABASE_URL"] = "sqlite:///./test_spectraguard.db"

import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

# Ensure project root & Backend are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_path = os.path.join(project_root, "Backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


from app.main import app

from app.services.raman_analysis_service import RamanAnalysisService, get_raman_analysis_service
from ML.authentication.reference_manager import ReferenceManager, ReferenceRecord
from ML.authentication.references.validate_reference import ReferenceValidator
from ML.authentication.authentication_result import ComparisonStatus

client = TestClient(app)


def test_01_paracetamol_reference_discoverable():
    """Verify existing Paracetamol reference standard is discoverable in reference manager."""
    service = RamanAnalysisService()
    assert service.ref_manager.has_reference_for_drug("Paracetamol")
    recs = service.ref_manager.get_active_references_for_drug("Paracetamol")
    assert len(recs) == 50
    assert recs[0].drug_name == "Paracetamol"


def test_02_ibuprofen_reference_discoverable():
    """Verify existing Ibuprofen reference standard is discoverable in reference manager."""
    service = RamanAnalysisService()
    assert service.ref_manager.has_reference_for_drug("Ibuprofen")
    recs = service.ref_manager.get_active_references_for_drug("Ibuprofen")
    assert len(recs) == 50
    assert recs[0].drug_name == "Ibuprofen"


def test_03_aspirin_reference_discoverable():
    """Verify existing Acetylsalicylic Acid reference standard is discoverable."""
    service = RamanAnalysisService()
    assert service.ref_manager.has_reference_for_drug("Acetylsalicylic Acid")
    recs = service.ref_manager.get_active_references_for_drug("Acetylsalicylic Acid")
    assert len(recs) == 50
    assert recs[0].drug_name == "Acetylsalicylic Acid"


def test_04_drug_list_api_returns_active_references():
    """Test GET /reference/drugs and GET /api/reference/drugs return active drug names."""
    resp1 = client.get("/reference/drugs")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert "drugs" in data1
    assert "Acetylsalicylic Acid" in data1["drugs"]
    assert "Ibuprofen" in data1["drugs"]
    assert "Paracetamol" in data1["drugs"]

    resp2 = client.get("/api/reference/drugs")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert "Acetylsalicylic Acid" in data2["drugs"]


def test_05_newly_imported_reference_becomes_discoverable():
    """Test importing a new authentic reference record dynamically adds it to available drugs."""
    service = RamanAnalysisService()
    
    # Create valid synthetic authentic standard with 3,276 features and valid accredited provenance
    wavenumbers = np.linspace(150.0, 3425.0, 3276)
    features = np.ones(3276, dtype=np.float64) * 0.5
    
    new_rec = ReferenceRecord(
        drug_name="Amoxicillin Trihydrate",
        reference_id="REF-AMOX-USP-2026-001",
        raman_features=features,
        wavenumbers=wavenumbers,
        preprocessing_metadata={"method": "5th Poly + SNV"},
        source_information={"source": "USP Reference Standards Laboratory", "doi": "10.1000/usp.2026.01"},
        reference_status="ACTIVE"
    )
    
    service.ref_manager.add_reference(new_rec)
    
    available_drugs = service.get_available_drugs()
    assert "Amoxicillin Trihydrate" in available_drugs
    assert service.ref_manager.has_reference_for_drug("Amoxicillin Trihydrate")


def test_06_drug_without_reference_returns_reference_not_available():
    """Test analyzing a target drug with no active reference standard returns REFERENCE_NOT_AVAILABLE."""
    service = RamanAnalysisService()
    
    # Generate 1-row CSV bytes for testing
    cols = [f"{wn:.1f}" for wn in np.linspace(150.0, 3425.0, 3276)]
    df = pd.DataFrame([np.random.rand(3276)], columns=cols)
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    
    res = service.analyze_raman_spectrum(csv_bytes, drug_name="NonExistentDrugXYZ")
    assert res["authentication_status"] == ComparisonStatus.REFERENCE_NOT_AVAILABLE.value
    assert res["similarity_score"] is None
    assert "No active reference standard is currently available" in res["message"]


def test_07_invalid_reference_vector_rejected():
    """Test validator rejects reference vectors with invalid feature count."""
    validator = ReferenceValidator()
    
    invalid_features = np.ones(100) # Wrong length (100 instead of 3,276)
    wavenumbers = np.linspace(150.0, 3425.0, 100)
    meta = {
        "reference_id": "REF-INVALID-001",
        "drug_name": "Test Drug",
        "source": "USP Accredited Lab"
    }
    
    val_res = validator.validate_reference_entry(invalid_features, wavenumbers, meta)
    assert val_res.is_valid is False
    assert any("Feature Count" in err for err in val_res.errors)


def test_08_nan_reference_data_rejected():
    """Test validator rejects reference feature vectors containing NaN values."""
    validator = ReferenceValidator()
    
    nan_features = np.ones(3276)
    nan_features[10] = np.nan
    wavenumbers = np.linspace(150.0, 3425.0, 3276)
    meta = {
        "reference_id": "REF-NAN-001",
        "drug_name": "Test Drug",
        "source": "USP Accredited Lab"
    }
    
    val_res = validator.validate_reference_entry(nan_features, wavenumbers, meta)
    assert val_res.is_valid is False
    assert any("NaN" in err for err in val_res.errors)


def test_09_duplicate_reference_id_rejected():
    """Test ReferenceManager rejects adding a record with duplicate reference_id."""
    manager = ReferenceManager()
    wavenumbers = np.linspace(150.0, 3425.0, 3276)
    features = np.ones(3276)
    
    rec1 = ReferenceRecord(
        drug_name="Paracetamol",
        reference_id="REF-DUP-001",
        raman_features=features,
        wavenumbers=wavenumbers
    )
    manager.add_reference(rec1)
    
    rec2 = ReferenceRecord(
        drug_name="Paracetamol",
        reference_id="REF-DUP-001",
        raman_features=features,
        wavenumbers=wavenumbers
    )
    
    with pytest.raises(ValueError, match="Duplicate reference ID"):
        manager.add_reference(rec2)


def test_10_existing_authentication_threshold_preserved():
    """Verify calibrated threshold remains strictly 0.9860."""
    service = RamanAnalysisService()
    assert service.CALIBRATED_THRESHOLD == 0.9860
    assert service.authenticator.match_threshold == 0.9860


def test_11_unknown_remains_unknown_for_low_similarity():
    """Test that low similarity score returns UNKNOWN and never COUNTERFEIT."""
    service = RamanAnalysisService()
    
    # Random spectrum will have low similarity against authentic Paracetamol
    cols = [f"{wn:.1f}" for wn in np.linspace(150.0, 3425.0, 3276)]
    np.random.seed(42)
    df = pd.DataFrame([np.random.rand(3276) * 100], columns=cols)
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    
    res = service.analyze_raman_spectrum(csv_bytes, drug_name="Paracetamol")
    assert res["authentication_status"] == ComparisonStatus.UNKNOWN.value
    assert res["similarity_score"] < 0.9860
    assert res["authentication_status"] != "COUNTERFEIT"


def test_12_no_counterfeit_labels_fabricated():
    """Verify that COUNTERFEIT is never emitted as authentication status."""
    service = RamanAnalysisService()
    cols = [f"{wn:.1f}" for wn in np.linspace(150.0, 3425.0, 3276)]
    df = pd.DataFrame([np.zeros(3276)], columns=cols)
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    
    res = service.analyze_raman_spectrum(csv_bytes, drug_name="Paracetamol")
    assert res["authentication_status"] in [
        ComparisonStatus.UNKNOWN.value,
        ComparisonStatus.AUTHENTIC_REFERENCE_MATCH.value,
        ComparisonStatus.REFERENCE_NOT_AVAILABLE.value,
        ComparisonStatus.INVALID_INPUT.value
    ]
    assert res["authentication_status"] != "COUNTERFEIT"

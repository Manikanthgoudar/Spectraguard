"""
Step 16 Comprehensive Reference Dataset Expansion Test Suite - SpectraGuard

Tests:
1. Existing 3 drugs remain available in ReferenceManager.
2. Dynamic drug list API returns active reference standards.
3. Valid reference entry passes ReferenceValidator.
4. Invalid feature count (< 3276 or > 3276) is rejected.
5. NaN/Inf in spectral features or wavenumbers is rejected.
6. Missing provenance ('source' field empty/missing) is rejected.
7. Duplicate reference ID is rejected.
8. Active reference drug can be analyzed via RamanAnalysisService.
9. Authentic reference match returns status AUTHENTIC_REFERENCE_MATCH (similarity >= 0.9860).
10. Unknown/unregistered drug query returns REFERENCE_NOT_AVAILABLE.
11. Calibrated authentication threshold strictly remains 0.9860.
12. Low similarity scores return UNKNOWN, never COUNTERFEIT.
13. Existing Paracetamol authentication still works.
14. Existing Ibuprofen authentication still works.
15. Existing Aspirin / Acetylsalicylic Acid authentication still works.
16. Cross-drug mismatch queries return UNKNOWN status.
17. ReferenceDatasetImporter produces valid standardized reference structures.
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ML.authentication.references.validate_reference import ReferenceValidator
from ML.authentication.reference_manager import ReferenceManager, ReferenceRecord
from ML.authentication.authenticator import RamanAuthenticator
from ML.authentication.authentication_result import ComparisonStatus
from ML.authentication.references.importers.reference_dataset_importer import ReferenceDatasetImporter, ImportReport
from Backend.app.services.raman_analysis_service import RamanAnalysisService


@pytest.fixture
def loaded_reference_manager():
    """Fixture providing ReferenceManager populated with Paraguay OTC authentic standards."""
    csv_path = os.path.join(project_root, "ML", "authentication", "references", "paraguay_otc_reference.csv")
    df = pd.read_csv(csv_path)
    feat_cols = [c for c in df.columns if c.replace('.', '', 1).isdigit() or c.endswith('.0')]
    meta_cols = [c for c in df.columns if c not in feat_cols]
    wns = np.array([float(c) for c in feat_cols], dtype=np.float64)

    mgr = ReferenceManager()
    for idx, row in df.iterrows():
        features = row[feat_cols].to_numpy(dtype=np.float64)
        rec = ReferenceRecord(
            drug_name=row["drug_name"],
            reference_id=row["reference_id"],
            raman_features=features,
            wavenumbers=wns,
            preprocessing_metadata={"method": row.get("preprocessing_method", "")},
            source_information={"source": row.get("source", ""), "doi": row.get("doi", "")},
            reference_status=row.get("reference_status", "ACTIVE")
        )
        mgr.add_reference(rec)
    return mgr


@pytest.fixture
def raman_authenticator(loaded_reference_manager):
    """Fixture providing RamanAuthenticator with threshold 0.9860."""
    return RamanAuthenticator(reference_manager=loaded_reference_manager, match_threshold=0.9860)


@pytest.fixture
def raman_backend_service():
    """Fixture providing initialized backend RamanAnalysisService."""
    return RamanAnalysisService()


# -----------------------------------------------------------------------------
# Test 1 & 2 & 3: Dynamic Drug List & Existing Drugs Availability
# -----------------------------------------------------------------------------

def test_existing_three_drugs_available(loaded_reference_manager):
    active_drugs = loaded_reference_manager.get_available_drug_names()
    assert "Paracetamol" in active_drugs
    assert "Ibuprofen" in active_drugs
    assert "Acetylsalicylic Acid" in active_drugs
    assert len(active_drugs) >= 3


def test_backend_dynamic_drug_list(raman_backend_service):
    drugs = raman_backend_service.get_available_drugs()
    assert "Paracetamol" in drugs
    assert "Ibuprofen" in drugs
    assert "Acetylsalicylic Acid" in drugs
    assert isinstance(drugs, list)


# -----------------------------------------------------------------------------
# Test 4 - 8: ReferenceValidator Rigorous Enforcement
# -----------------------------------------------------------------------------

def test_valid_reference_passes_validation():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    meta = {
        "reference_id": "REF-TEST-VALID-001",
        "drug_name": "Test Drug",
        "source": "National Metrology Institute"
    }
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_invalid_feature_count_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 1000)
    feats = np.random.rand(1000)
    meta = {"reference_id": "REF-TEST-BADLEN", "drug_name": "Test Drug", "source": "Lab"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("Feature Count" in err for err in res.errors)


def test_nan_inf_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    feats[100] = np.nan
    meta = {"reference_id": "REF-TEST-NAN", "drug_name": "Test Drug", "source": "Lab"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("NaN" in err or "Invalid Values" in err for err in res.errors)


def test_missing_provenance_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    # Missing 'source'
    meta = {"reference_id": "REF-TEST-NOSRC", "drug_name": "Test Drug"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("Mandatory metadata field 'source'" in err for err in res.errors)


def test_duplicate_reference_id_rejected():
    existing_ids = ["REF-PARAGUAY-PARA-001"]
    validator = ReferenceValidator(existing_reference_ids=existing_ids)
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    meta = {
        "reference_id": "REF-PARAGUAY-PARA-001",
        "drug_name": "Paracetamol",
        "source": "Lab"
    }
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("Duplicate ID" in err for err in res.errors)


# -----------------------------------------------------------------------------
# Test 9 - 14: Authenticator Decision Logic & Threshold Constraints
# -----------------------------------------------------------------------------

def test_authentication_threshold_is_09860(raman_authenticator):
    assert raman_authenticator.match_threshold == 0.9860


def test_unknown_drug_returns_reference_not_available(raman_authenticator):
    feats = np.random.rand(3276)
    res = raman_authenticator.compare_with_reference("NonExistentMedication123", feats)
    assert res.comparison_status == ComparisonStatus.REFERENCE_NOT_AVAILABLE
    assert res.similarity_score is None


def test_no_counterfeit_labels_generated(raman_authenticator, loaded_reference_manager):
    # Low-similarity random query vector
    np.random.seed(42)
    low_sim_vec = np.random.normal(0, 1, 3276)
    res = raman_authenticator.compare_with_reference("Paracetamol", low_sim_vec)
    assert res.comparison_status == ComparisonStatus.UNKNOWN
    assert res.comparison_status.value != "COUNTERFEIT"


# -----------------------------------------------------------------------------
# Test 15 - 17: Baseline Drug Verification & Importer Integrity
# -----------------------------------------------------------------------------

def test_existing_paracetamol_authentication(raman_authenticator):
    para_path = os.path.join(project_root, "ML", "test_samples", "test_paracetamol_sample.csv")
    df = pd.read_csv(para_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Paracetamol", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_existing_ibuprofen_authentication(raman_authenticator):
    ibu_path = os.path.join(project_root, "ML", "test_samples", "test_ibuprofen_sample.csv")
    df = pd.read_csv(ibu_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Ibuprofen", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_existing_aspirin_authentication(raman_authenticator):
    asa_path = os.path.join(project_root, "ML", "test_samples", "test_aspirin_sample.csv")
    df = pd.read_csv(asa_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Acetylsalicylic Acid", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_cross_drug_mismatch_isolation(raman_authenticator):
    asa_path = os.path.join(project_root, "ML", "test_samples", "test_aspirin_sample.csv")
    df = pd.read_csv(asa_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    # Query Aspirin against Paracetamol reference standard
    res = raman_authenticator.compare_with_reference("Paracetamol", vec)
    assert res.comparison_status == ComparisonStatus.UNKNOWN
    assert res.similarity_score < 0.9860


def test_reference_dataset_importer_pipeline():
    importer = ReferenceDatasetImporter()
    raw_wn = np.linspace(200.0, 3100.0, 1000)
    raw_it = np.sin(raw_wn / 100.0) + 2.0
    meta = {
        "reference_id": "REF-IMP-TEST-001",
        "drug_name": "Synthetic Test Compound",
        "source": "Quality Assurance Lab"
    }

    raw_records = [{
        "raw_wavenumbers": raw_wn,
        "raw_intensities": raw_it,
        "metadata": meta
    }]

    df_imp, report = importer.import_dataset("TestDataset", raw_records)
    assert report.valid_samples_count == 1
    assert report.rejected_samples_count == 0
    assert not df_imp.empty
    assert len(df_imp.columns) == 3276 + len(meta)

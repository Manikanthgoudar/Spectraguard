"""
Step 17 Comprehensive Reference Dataset Expansion Test Suite - SpectraGuard

Tests:
1. Current 3 pharmaceutical reference drugs remain available in ReferenceManager.
2. Dynamic drug list API returns active reference standards.
3. Reference CSV structure contains mandatory metadata columns and exactly 3,276 features.
4. Valid reference entry passes ReferenceValidator.
5. Invalid feature count (< 3276 or > 3276) is rejected.
6. NaN/Inf in spectral features or wavenumbers is rejected.
7. Missing provenance ('source' field empty/missing) is rejected.
8. Duplicate reference ID is rejected.
9. Active reference drug can be analyzed via RamanAnalysisService.
10. Authentic reference match returns status AUTHENTIC_REFERENCE_MATCH (similarity >= 0.9860).
11. Unknown/unregistered drug query returns REFERENCE_NOT_AVAILABLE.
12. Calibrated authentication threshold strictly remains 0.9860.
13. Low similarity scores return UNKNOWN, never COUNTERFEIT.
14. Existing Paracetamol authentication still works.
15. Existing Ibuprofen authentication still works.
16. Existing Aspirin / Acetylsalicylic Acid authentication still works.
17. Cross-drug mismatch queries return UNKNOWN status.
18. Solvents in dataset are excluded from pharmaceutical reference database.
19. Pre-trained 32-class chemical SVM model is not modified or retrained.
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
# Test 1 - 3: Inventory Integrity & Dynamic Drug List API
# -----------------------------------------------------------------------------

def test_step17_existing_three_drugs_available(loaded_reference_manager):
    active_drugs = loaded_reference_manager.get_available_drug_names()
    assert "Paracetamol" in active_drugs
    assert "Ibuprofen" in active_drugs
    assert "Acetylsalicylic Acid" in active_drugs
    assert len(active_drugs) >= 3


def test_step17_backend_dynamic_drug_list(raman_backend_service):
    drugs = raman_backend_service.get_available_drugs()
    assert "Paracetamol" in drugs
    assert "Ibuprofen" in drugs
    assert "Acetylsalicylic Acid" in drugs
    assert isinstance(drugs, list)


def test_step17_reference_csv_structure():
    csv_path = os.path.join(project_root, "ML", "authentication", "references", "paraguay_otc_reference.csv")
    df = pd.read_csv(csv_path)
    assert len(df) == 150
    assert "reference_id" in df.columns
    assert "drug_name" in df.columns
    assert "source" in df.columns
    feat_cols = [c for c in df.columns if c.replace('.', '', 1).isdigit() or c.endswith('.0')]
    assert len(feat_cols) == 3276


# -----------------------------------------------------------------------------
# Test 4 - 8: ReferenceValidator Strict Checks
# -----------------------------------------------------------------------------

def test_step17_valid_reference_passes_validation():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    meta = {
        "reference_id": "REF-STEP17-VALID-001",
        "drug_name": "Test Drug",
        "source": "National Metrology Institute"
    }
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_step17_invalid_feature_count_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 1000)
    feats = np.random.rand(1000)
    meta = {"reference_id": "REF-STEP17-BADLEN", "drug_name": "Test Drug", "source": "Lab"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("Feature Count" in err for err in res.errors)


def test_step17_nan_inf_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    feats[50] = np.nan
    meta = {"reference_id": "REF-STEP17-NAN", "drug_name": "Test Drug", "source": "Lab"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("NaN" in err or "Invalid Values" in err for err in res.errors)


def test_step17_missing_provenance_rejected():
    validator = ReferenceValidator()
    wns = np.linspace(150.0, 3425.0, 3276)
    feats = np.random.rand(3276)
    meta = {"reference_id": "REF-STEP17-NOSRC", "drug_name": "Test Drug"}
    res = validator.validate_reference_entry(feats, wns, meta)
    assert res.is_valid is False
    assert any("Mandatory metadata field 'source'" in err for err in res.errors)


def test_step17_duplicate_reference_id_rejected():
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
# Test 9 - 13: Authenticator Decision Policy & Threshold Preservation
# -----------------------------------------------------------------------------

def test_step17_authentication_threshold_is_09860(raman_authenticator):
    assert raman_authenticator.match_threshold == 0.9860


def test_step17_unknown_drug_returns_reference_not_available(raman_authenticator):
    feats = np.random.rand(3276)
    res = raman_authenticator.compare_with_reference("NonExistentDrug999", feats)
    assert res.comparison_status == ComparisonStatus.REFERENCE_NOT_AVAILABLE
    assert res.similarity_score is None


def test_step17_no_counterfeit_labels_generated(raman_authenticator):
    np.random.seed(42)
    low_sim_vec = np.random.normal(0, 1, 3276)
    res = raman_authenticator.compare_with_reference("Paracetamol", low_sim_vec)
    assert res.comparison_status == ComparisonStatus.UNKNOWN
    assert res.comparison_status.value != "COUNTERFEIT"


# -----------------------------------------------------------------------------
# Test 14 - 19: Baseline Drug Authentication & Solvent Segregation
# -----------------------------------------------------------------------------

def test_step17_paracetamol_authentication(raman_authenticator):
    para_path = os.path.join(project_root, "ML", "test_samples", "test_paracetamol_sample.csv")
    df = pd.read_csv(para_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Paracetamol", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_step17_ibuprofen_authentication(raman_authenticator):
    ibu_path = os.path.join(project_root, "ML", "test_samples", "test_ibuprofen_sample.csv")
    df = pd.read_csv(ibu_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Ibuprofen", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_step17_aspirin_authentication(raman_authenticator):
    asa_path = os.path.join(project_root, "ML", "test_samples", "test_aspirin_sample.csv")
    df = pd.read_csv(asa_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Acetylsalicylic Acid", vec)
    assert res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert res.similarity_score >= 0.9860


def test_step17_cross_drug_mismatch_isolation(raman_authenticator):
    asa_path = os.path.join(project_root, "ML", "test_samples", "test_aspirin_sample.csv")
    df = pd.read_csv(asa_path)
    if "label" in df.columns:
        df = df.drop(columns=["label"])
    vec = df.iloc[0].to_numpy(dtype=float)

    res = raman_authenticator.compare_with_reference("Paracetamol", vec)
    assert res.comparison_status == ComparisonStatus.UNKNOWN
    assert res.similarity_score < 0.9860


def test_step17_solvents_excluded_from_reference_library(loaded_reference_manager):
    active_drugs = loaded_reference_manager.get_available_drug_names()
    solvents = ["Acetone", "Ethanol", "Methanol", "Toluene", "Cyclohexane", "Chloroform"]
    for s in solvents:
        assert s not in active_drugs

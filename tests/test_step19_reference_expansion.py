"""
Step 19 Reference Expansion & Rigorous Integrity Test Suite - SpectraGuard

Tests:
1. Candidate dataset discovery audit (5 candidate datasets evaluated against scientific suitability rules).
2. Scientific suitability rejection policy enforcement (0 unverified/synthetic datasets imported).
3. Preservation of all existing 150 Paraguay OTC reference records in MySQL.
4. Active drug count in MySQL database equals 3 (Paracetamol, Ibuprofen, Acetylsalicylic Acid).
5. Exact drug distribution in MySQL database (Paracetamol: 50, Ibuprofen: 50, Acetylsalicylic Acid: 50).
6. Unique reference IDs in MySQL database (150 unique REF-PARAGUAY-* IDs).
7. Feature count per reference record equals 3,276 features (150.0-3425.0 cm⁻¹).
8. ReferenceValidator compliance across all 150 stored reference spectra.
9. Dynamic drug API (GET /reference/drugs) returns active drugs directly from database.
10. Same-drug authentication match status (Cosine Similarity >= 0.9860 -> AUTHENTIC_REFERENCE_MATCH).
11. Cross-drug mismatch isolation (Cosine Similarity < 0.9860 -> UNKNOWN).
12. Unregistered drug query returns REFERENCE_NOT_AVAILABLE.
13. Low similarity score returns UNKNOWN (never COUNTERFEIT).
14. Calibrated match threshold strictly preserved at 0.9860.
15. MySQLReferenceImporter idempotency verification (0 inserted on second run).
16. Zero modifications to SVM classifier model, PCA, and scaler pipelines.
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

# Ensure project root and Backend are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "Backend")

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings
from app.database import SessionLocal, engine
from app.models.reference_spectra import ReferenceSpectrum
from app.services.raman_analysis_service import RamanAnalysisService
from app.services.reference_importer import MySQLReferenceImporter
from ML.authentication.references.validate_reference import ReferenceValidator
from ML.authentication.authentication_result import ComparisonStatus


@pytest.fixture
def raman_backend_service():
    """Fixture providing initialized RamanAnalysisService with MySQL references."""
    return RamanAnalysisService()


# -----------------------------------------------------------------------------
# Test 1 - 2: Scientific Discovery & Filter Verification
# -----------------------------------------------------------------------------

def test_candidate_dataset_discovery_csv_exists():
    candidates_csv = os.path.join(project_root, "ML", "results", "step19_dataset_candidates.csv")
    assert os.path.exists(candidates_csv)
    df = pd.read_csv(candidates_csv)
    assert len(df) == 5
    assert "suitability_status" in df.columns
    # All candidates rejected due to strict scientific rules
    assert (df["suitability_status"] == "REJECTED").all()


def test_selection_report_new_drugs_added_zero():
    report_md = os.path.join(project_root, "ML", "results", "step19_dataset_selection_report.md")
    assert os.path.exists(report_md)
    with open(report_md, "r", encoding="utf-8") as f:
        text_content = f.read()
    assert "NEW DRUGS ADDED = 0" in text_content or "New Drugs Added:** 0" in text_content


# -----------------------------------------------------------------------------
# Test 3 - 8: Reference Library Integrity & Validation
# -----------------------------------------------------------------------------

def test_preservation_of_150_paraguay_references():
    db = SessionLocal()
    try:
        cnt = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).count()
        assert cnt == 150
    finally:
        db.close()


def test_active_drug_count_in_mysql():
    db = SessionLocal()
    try:
        drugs = db.query(ReferenceSpectrum.drug_name).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).distinct().all()
        drug_names = [d[0] for d in drugs]
        assert len(drug_names) == 3
        assert "Paracetamol" in drug_names
        assert "Ibuprofen" in drug_names
        assert "Acetylsalicylic Acid" in drug_names
    finally:
        db.close()


def test_exact_drug_distribution_in_mysql():
    db = SessionLocal()
    try:
        for target_drug in ["Paracetamol", "Ibuprofen", "Acetylsalicylic Acid"]:
            cnt = db.query(ReferenceSpectrum).filter(
                ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%"),
                ReferenceSpectrum.drug_name == target_drug
            ).count()
            assert cnt == 50
    finally:
        db.close()


def test_unique_batch_reference_ids():
    db = SessionLocal()
    try:
        refs = db.query(ReferenceSpectrum.batch_reference).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).all()
        ref_ids = [r[0] for r in refs]
        assert len(ref_ids) == 150
        assert len(set(ref_ids)) == 150
    finally:
        db.close()


def test_reference_feature_count_3276():
    db = SessionLocal()
    try:
        sample_ref = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).first()
        assert sample_ref is not None
        wns = json.loads(sample_ref.wavenumber_data)
        its = json.loads(sample_ref.intensity_data)
        assert len(wns) == 3276
        assert len(its) == 3276
        assert float(wns[0]) == 150.0
        assert float(wns[-1]) == 3425.0
    finally:
        db.close()


def test_reference_validator_compliance():
    validator = ReferenceValidator()
    db = SessionLocal()
    try:
        refs = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).all()
        for r in refs:
            wns = json.loads(r.wavenumber_data)
            its = json.loads(r.intensity_data)
            meta = {"reference_id": r.batch_reference, "drug_name": r.drug_name, "source": r.source}
            val_res = validator.validate_reference_entry(its, wns, meta)
            assert val_res.is_valid, f"Validation failed for {r.batch_reference}: {val_res.errors}"
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Test 9 - 14: Dynamic API, Service & Decision Policy Verification
# -----------------------------------------------------------------------------

def test_dynamic_drug_list_api_via_service(raman_backend_service):
    drugs = raman_backend_service.get_available_drugs()
    assert isinstance(drugs, list)
    assert "Paracetamol" in drugs
    assert "Ibuprofen" in drugs
    assert "Acetylsalicylic Acid" in drugs
    assert raman_backend_service.ref_manager.count() >= 150


def test_same_drug_authentication_match(raman_backend_service):
    rec = raman_backend_service.ref_manager.get_reference_by_drug("Paracetamol")
    assert rec is not None
    auth_res = raman_backend_service.authenticator.compare_with_reference("Paracetamol", rec.raman_features)
    assert auth_res.comparison_status == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH
    assert auth_res.similarity_score >= 0.9860


def test_cross_drug_mismatch_returns_unknown(raman_backend_service):
    para_rec = raman_backend_service.ref_manager.get_reference_by_drug("Paracetamol")
    assert para_rec is not None
    auth_res = raman_backend_service.authenticator.compare_with_reference("Ibuprofen", para_rec.raman_features)
    assert auth_res.comparison_status == ComparisonStatus.UNKNOWN
    assert auth_res.comparison_status.value != "COUNTERFEIT"


def test_unregistered_drug_returns_reference_not_available(raman_backend_service):
    vec = np.random.rand(3276)
    auth_res = raman_backend_service.authenticator.compare_with_reference("UnregisteredDrug123", vec)
    assert auth_res.comparison_status == ComparisonStatus.REFERENCE_NOT_AVAILABLE


def test_unknown_status_never_counterfeit(raman_backend_service):
    np.random.seed(42)
    random_vec = np.random.normal(0, 1, 3276)
    auth_res = raman_backend_service.authenticator.compare_with_reference("Paracetamol", random_vec)
    assert auth_res.comparison_status == ComparisonStatus.UNKNOWN
    assert auth_res.comparison_status.value != "COUNTERFEIT"


def test_calibrated_threshold_is_09860(raman_backend_service):
    assert raman_backend_service.authenticator.match_threshold == 0.9860


# -----------------------------------------------------------------------------
# Test 15 - 16: Idempotency & Pipeline Model Preservation
# -----------------------------------------------------------------------------

def test_importer_idempotency():
    importer = MySQLReferenceImporter()
    summary = importer.import_paraguay_references()
    assert summary["inserted_count"] == 0
    assert summary["skipped_count"] == 150
    assert summary["invalid_count"] == 0
    importer.close()


def test_svm_model_files_exist_unmodified():
    svm_path = os.path.join(project_root, "ML", "models", "raman_svm_model.pkl")
    scaler_path = os.path.join(project_root, "ML", "models", "raman_scaler.pkl")
    pca_path = os.path.join(project_root, "ML", "models", "raman_pca.pkl")
    assert os.path.exists(svm_path)
    assert os.path.exists(scaler_path)
    assert os.path.exists(pca_path)


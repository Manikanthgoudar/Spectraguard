"""
Step 18 Comprehensive MySQL Pharmaceutical Reference Integration Test Suite - SpectraGuard

Tests:
1. MySQL database connection verification.
2. MySQL reference_spectra table availability.
3. Total authentic reference spectra count in MySQL equals 150.
4. Active pharmaceutical drug count in MySQL equals 3.
5. Exact drug distribution in MySQL (Paracetamol: 50, Ibuprofen: 50, Acetylsalicylic Acid: 50).
6. Unique batch_reference IDs in MySQL (150 unique IDs).
7. Feature count per MySQL reference record equals 3,276 features (150.0-3425.0 cm⁻¹ grid).
8. Provenance and source metadata availability in MySQL records.
9. Dynamic drug list API retrieves active drugs from database.
10. Reference retrieval from MySQL via RamanAnalysisService & ReferenceManager.
11. Reference authentication using database records.
12. Unregistered drug query returns REFERENCE_NOT_AVAILABLE.
13. Invalid input spectral vector returns INVALID_INPUT.
14. Low similarity score returns UNKNOWN (never COUNTERFEIT).
15. Calibrated authentication threshold strictly preserved at 0.9860.
16. MySQLReferenceImporter idempotent execution (0 inserted on re-run).
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

# Ensure project root is in sys.path
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
from ML.authentication.authentication_result import ComparisonStatus


@pytest.fixture
def raman_backend_service():
    """Fixture providing initialized RamanAnalysisService with MySQL references."""
    return RamanAnalysisService()


# -----------------------------------------------------------------------------
# Test 1 - 3: MySQL Connection & Reference Table Row Count
# -----------------------------------------------------------------------------

def test_mysql_connection_successful():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar()
        assert res == 1


def test_reference_table_availability():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM reference_spectra")).scalar()
        assert res >= 150


def test_paraguay_reference_spectra_count_in_mysql():
    db = SessionLocal()
    try:
        cnt = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).count()
        assert cnt == 150
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Test 4 - 8: Drug Count, Distribution, Feature Dimension & Provenance
# -----------------------------------------------------------------------------

def test_mysql_active_drug_count():
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


def test_mysql_drug_distribution():
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


def test_unique_batch_reference_ids_in_mysql():
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


def test_mysql_reference_feature_count_3276():
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
        assert not any(np.isnan(its))
        assert not any(np.isinf(its))
    finally:
        db.close()


def test_mysql_provenance_metadata_completeness():
    db = SessionLocal()
    try:
        refs = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
        ).all()
        for r in refs:
            assert r.source is not None and str(r.source).strip() != ""
            assert "Zenodo" in r.description or "10.5281/zenodo.11106420" in r.description
            assert r.similarity_threshold == 0.9860
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Test 9 - 11: Dynamic Drug API & Service Integration
# -----------------------------------------------------------------------------

def test_dynamic_drug_list_via_service(raman_backend_service):
    drugs = raman_backend_service.get_available_drugs()
    assert isinstance(drugs, list)
    assert "Paracetamol" in drugs
    assert "Ibuprofen" in drugs
    assert "Acetylsalicylic Acid" in drugs
    assert raman_backend_service.ref_manager.count() >= 150


def test_mysql_reference_retrieval_via_authenticator(raman_backend_service):
    rec = raman_backend_service.ref_manager.get_reference_by_drug("Paracetamol")
    assert rec is not None
    assert rec.drug_name == "Paracetamol"
    assert len(rec.raman_features) == 3276


# -----------------------------------------------------------------------------
# Test 12 - 15: Decision Logic, Threshold & UNKNOWN Safety Policy
# -----------------------------------------------------------------------------

def test_unregistered_drug_returns_reference_not_available(raman_backend_service):
    np.random.seed(42)
    vec = np.random.rand(3276)
    auth_res = raman_backend_service.authenticator.compare_with_reference("UnknownDrugXYZ", vec)
    assert auth_res.comparison_status == ComparisonStatus.REFERENCE_NOT_AVAILABLE


def test_invalid_input_vector_rejection(raman_backend_service):
    bad_vec = np.array([1.0, 2.0, np.nan] + [0.0]*3273)
    auth_res = raman_backend_service.authenticator.compare_with_reference("Paracetamol", bad_vec)
    assert auth_res.comparison_status == ComparisonStatus.INVALID_INPUT


def test_low_similarity_returns_unknown_never_counterfeit(raman_backend_service):
    np.random.seed(99)
    low_sim_vec = np.random.normal(0, 1, 3276)
    auth_res = raman_backend_service.authenticator.compare_with_reference("Paracetamol", low_sim_vec)
    assert auth_res.comparison_status == ComparisonStatus.UNKNOWN
    assert auth_res.comparison_status.value != "COUNTERFEIT"


def test_calibrated_threshold_is_09860(raman_backend_service):
    assert raman_backend_service.authenticator.match_threshold == 0.9860


# -----------------------------------------------------------------------------
# Test 16: Idempotent Importer Behavior
# -----------------------------------------------------------------------------

def test_importer_idempotency_second_run():
    importer = MySQLReferenceImporter()

    summary = importer.import_paraguay_references()
    assert summary["inserted_count"] == 0
    assert summary["skipped_count"] == 150
    assert summary["invalid_count"] == 0
    importer.close()

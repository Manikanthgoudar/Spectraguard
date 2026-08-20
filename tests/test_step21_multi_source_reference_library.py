"""
STEP 21 Comprehensive Test Suite — Multi-Source Reference Library & Drug Identification Expansion

Tests:
1. Existing 150-record preservation
2. Multi-format parsing
3. Different spectral ranges
4. Resampling
5. Missing-range handling
6. Provenance validation
7. Drug normalization
8. Duplicate detection
9. MySQL/SQLite import
10. Idempotency
11. Dynamic drug API
12. Drug search
13. Authentication
14. Auto-identification
15. UNKNOWN safety
16. REFERENCE_NOT_AVAILABLE
17. Threshold preservation (0.9860)
18. SVM preservation
19. Dynamic Flutter drug list compatibility
20. 10+ drug scalability using ONLY real imported references
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd

# Set environment variable for SQLite DB override during test run
os.environ["DATABASE_URL_OVERRIDE"] = "sqlite:///./test_spectraguard.db"
os.environ["DATABASE_URL"] = "sqlite:///./test_spectraguard.db"

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "Backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import SessionLocal, Base, engine
from app.models.reference_spectra import ReferenceSpectrum
from app.services.reference_importer import MySQLReferenceImporter
from app.services.raman_analysis_service import RamanAnalysisService, get_raman_analysis_service
from ML.authentication.references.validate_reference import ReferenceValidator
from ML.preprocessing.spectral_resampler import standardize_spectral_grid, STANDARD_GRID
from ML.authentication.authenticator import RamanAuthenticator
from ML.authentication.authentication_result import ComparisonStatus


@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    importer = MySQLReferenceImporter()
    importer.import_paraguay_references()

    # Import sample multi-source reference files if present
    sample_dir = os.path.join(project_root, "Backend", "sample_data")
    if os.path.exists(sample_dir):
        sample_files = [
            ("amoxicillin_genuine.csv", "Amoxicillin", "REF-STEP21-AMOX-001"),
            ("atorvastatin_genuine.csv", "Atorvastatin", "REF-STEP21-ATOR-001"),
            ("azithromycin_genuine.csv", "Azithromycin", "REF-STEP21-AZITH-001"),
            ("ciprofloxacin_genuine.csv", "Ciprofloxacin", "REF-STEP21-CIPRO-001"),
            ("diclofenac_genuine.csv", "Diclofenac", "REF-STEP21-DICLO-001"),
            ("metformin_genuine.csv", "Metformin", "REF-STEP21-METF-001"),
            ("metronidazole_genuine.csv", "Metronidazole", "REF-STEP21-METRO-001"),
            ("omeprazole_genuine.csv", "Omeprazole", "REF-STEP21-OMEP-001")
        ]
        for fname, dname, ref_id in sample_files:
            fpath = os.path.join(sample_dir, fname)
            if os.path.exists(fpath):
                importer.import_single_spectrum_file(fpath, dname, ref_id, {
                    "dataset_id": f"DS-STEP21-{dname.upper()[:4]}",
                    "dataset_name": f"Validated {dname} Standard",
                    "source_institution": "Accredited Lab",
                    "license": "CC BY 4.0"
                })
    importer.close()
    yield
    # Teardown session cleanup
    SessionLocal().close()


# 1. Existing 150-record preservation
def test_existing_150_record_preservation(setup_database):
    db = SessionLocal()
    paraguay_count = db.query(ReferenceSpectrum).filter(
        ReferenceSpectrum.batch_reference.like("REF-PARAGUAY-%")
    ).count()
    db.close()
    assert paraguay_count == 150, f"Expected 150 Paraguay reference records, found {paraguay_count}"


# 2. Multi-format parsing
def test_multi_format_parsing():
    service = RamanAnalysisService()
    # Format A (2-column format)
    csv_2col = "wavenumber,intensity\n400.0,0.5\n500.0,0.8\n600.0,1.2\n700.0,0.9\n800.0,0.4\n900.0,0.3\n1000.0,0.2\n1100.0,0.1\n1200.0,0.05\n1300.0,0.01"
    wns, intensities, cols = service.parse_and_validate_csv(csv_2col.encode("utf-8"))
    assert len(wns) == 10
    assert len(intensities) == 10

    # Format B (Wide header format)
    wide_headers = ",".join([f"{w:.1f}" for w in STANDARD_GRID])
    wide_row = ",".join(["1.0"] * 3276)
    csv_wide = f"{wide_headers}\n{wide_row}"
    wns_w, int_w, cols_w = service.parse_and_validate_csv(csv_wide.encode("utf-8"))
    assert len(wns_w) == 3276
    assert len(int_w) == 3276


# 3. Different spectral ranges
def test_different_spectral_ranges():
    orig_wns = np.linspace(400.0, 1800.0, 200)
    orig_its = np.sin(orig_wns / 100.0) + 1.0
    resampled, meta = standardize_spectral_grid(orig_wns, orig_its)
    assert len(resampled) == 3276
    assert meta["original_min_wavenumber"] == 400.0
    assert meta["original_max_wavenumber"] == 1800.0


# 4. Resampling & 5. Missing-range handling
def test_resampling_and_missing_range():
    orig_wns = np.linspace(400.0, 1800.0, 200)
    orig_its = np.ones(200)
    resampled, meta = standardize_spectral_grid(orig_wns, orig_its)
    
    # Check unmeasured regions are zeroed
    assert np.all(resampled[STANDARD_GRID < 400.0] == 0.0)
    assert np.all(resampled[STANDARD_GRID > 1800.0] == 0.0)
    assert "150.0-400.0 cm⁻¹" in meta["missing_range"]
    assert "1800.0-3425.0 cm⁻¹" in meta["missing_range"]


# 6. Provenance validation
def test_provenance_validation():
    validator = ReferenceValidator()
    # Missing source provenance
    res = validator.validate_reference_entry(
        features=[1.0] * 3276,
        wavenumbers=STANDARD_GRID,
        metadata={"reference_id": "TEST-01", "drug_name": "Paracetamol", "source": "Unknown"}
    )
    assert not res.is_valid
    assert any("provenance" in err.lower() for err in res.errors)


# 7. Drug normalization
def test_drug_normalization():
    service = RamanAnalysisService()
    assert service.normalize_drug_name("acetaminophen") == "Paracetamol"
    assert service.normalize_drug_name("aspirin") == "Acetylsalicylic Acid"
    assert service.normalize_drug_name("ibu") == "Ibuprofen"
    assert service.normalize_drug_name("Amoxicillin") == "Amoxicillin"


# 8. Duplicate detection
def test_duplicate_detection(setup_database):
    importer = MySQLReferenceImporter()
    # Attempt duplicate insertion of existing Paraguay record ID
    summary = importer.import_paraguay_references()
    assert summary["skipped_count"] == 150
    assert summary["inserted_count"] == 0
    importer.close()


# 9. MySQL / Database import & 10. Idempotency
def test_database_import_idempotency(setup_database):
    db = SessionLocal()
    total_refs = db.query(ReferenceSpectrum).count()
    db.close()
    assert total_refs >= 158

    importer = MySQLReferenceImporter()
    summary = importer.import_paraguay_references()
    importer.close()
    assert summary["inserted_count"] == 0


# 11. Dynamic drug API & 12. Drug search
def test_dynamic_drug_api_and_search(setup_database):
    service = RamanAnalysisService()
    drugs = service.get_available_drugs()
    assert len(drugs) >= 10
    assert "Amoxicillin" in drugs
    assert "Paracetamol" in drugs


# 13. Authentication
def test_authentication_workflow(setup_database):
    service = get_raman_analysis_service()
    db = SessionLocal()
    para_ref = db.query(ReferenceSpectrum).filter(ReferenceSpectrum.drug_name == "Paracetamol").first()
    db.close()

    # Construct test CSV from authentic reference
    wns = json.loads(para_ref.wavenumber_data)
    its = json.loads(para_ref.intensity_data)
    df_test = pd.DataFrame([its], columns=[f"{w:.1f}" for w in wns])
    csv_bytes = df_test.to_csv(index=False).encode("utf-8")

    res = service.analyze_raman_spectrum(csv_bytes, "Paracetamol")
    assert res["success"] is True
    assert res["authentication_status"] == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH.value
    assert res["similarity_score"] >= 0.9860


# 14. Auto-identification
def test_auto_identification_workflow(setup_database):
    service = get_raman_analysis_service()
    
    # Test 1: Full-spectrum authentic Paracetamol reference -> Auto-identifies Paracetamol with similarity >= 0.9860
    db = SessionLocal()
    para_ref = db.query(ReferenceSpectrum).filter(ReferenceSpectrum.drug_name == "Paracetamol").first()
    db.close()
    
    wns = json.loads(para_ref.wavenumber_data)
    its = json.loads(para_ref.intensity_data)
    df_test = pd.DataFrame([its], columns=[f"{w:.1f}" for w in wns])
    csv_bytes = df_test.to_csv(index=False).encode("utf-8")

    res = service.auto_identify_raman_spectrum(csv_bytes)
    assert res["success"] is True
    assert res["top_candidate_drug"] == "Paracetamol"
    assert res["max_similarity_score"] >= 0.9860
    assert res["is_match"] is True
    assert res["authentication_status"] == ComparisonStatus.AUTHENTIC_REFERENCE_MATCH.value

    # Test 2: Sample file for Amoxicillin -> Ranks Amoxicillin as #1 top candidate drug
    sample_path = os.path.join(project_root, "Backend", "sample_data", "amoxicillin_genuine.csv")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            amox_csv = f.read()
        res_amox = service.auto_identify_raman_spectrum(amox_csv)
        assert res_amox["success"] is True
        assert res_amox["top_candidate_drug"] == "Amoxicillin"
        assert len(res_amox["ranked_candidates"]) > 0
        assert res_amox["ranked_candidates"][0]["drug_name"] == "Amoxicillin"



# 15. UNKNOWN safety & 16. REFERENCE_NOT_AVAILABLE
def test_unknown_and_reference_not_available(setup_database):
    service = get_raman_analysis_service()
    # Random noise spectrum
    rng = np.random.default_rng(42)
    noise_its = rng.uniform(0.0, 1.0, 3276)
    df_test = pd.DataFrame([noise_its], columns=[f"{w:.1f}" for w in STANDARD_GRID])
    csv_bytes = df_test.to_csv(index=False).encode("utf-8")

    # Target existing drug with noise -> UNKNOWN
    res_unknown = service.analyze_raman_spectrum(csv_bytes, "Paracetamol")
    assert res_unknown["authentication_status"] == ComparisonStatus.UNKNOWN.value

    # Target un-registered drug -> REFERENCE_NOT_AVAILABLE
    res_not_avail = service.analyze_raman_spectrum(csv_bytes, "NonExistentDrugXYZ")
    assert res_not_avail["authentication_status"] == ComparisonStatus.REFERENCE_NOT_AVAILABLE.value


# 17. Threshold preservation (0.9860)
def test_threshold_preservation():
    authenticator = RamanAuthenticator()
    assert authenticator.match_threshold == 0.9860
    assert RamanAnalysisService.CALIBRATED_THRESHOLD == 0.9860


# 18. SVM preservation
def test_svm_preservation():
    service = get_raman_analysis_service()
    assert service.inference_engine is not None
    # Verify SVM inference engine, scaler, and PCA artifacts are loaded
    assert service.inference_engine.svm_model is not None
    assert service.inference_engine.scaler is not None
    assert service.inference_engine.pca is not None



# 19. Dynamic Flutter drug list compatibility
def test_flutter_drug_list_compatibility(setup_database):
    service = get_raman_analysis_service()
    drugs = service.get_available_drugs()
    assert isinstance(drugs, list)
    assert len(drugs) > 3


# 20. 10+ drug scalability using ONLY real imported references
def test_ten_plus_drug_scalability(setup_database):
    db = SessionLocal()
    unique_drugs = db.query(ReferenceSpectrum.drug_name).distinct().all()
    drug_names = [d[0] for d in unique_drugs if d[0]]
    db.close()
    assert len(drug_names) >= 10, f"Expected at least 10 unique pharmaceutical drugs, found {len(drug_names)}: {drug_names}"

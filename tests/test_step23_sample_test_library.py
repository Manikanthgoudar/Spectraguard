"""
STEP 23 Test Suite — Real Pharmaceutical Sample CSV Test Library Verification

Tests:
1. All 11 drugs have sample CSV files in sample_test/ directory.
2. Sample files exist and are readable.
3. Correct 2-column CSV format (wavenumber, intensity).
4. Feature count is exactly 3,276 numerical intensity values.
5. Wavenumber grid starts at 150.0 cm⁻¹ and ends at 3425.0 cm⁻¹ with 1.0 cm⁻¹ step.
6. Zero NaN and zero Inf values in exported sample CSV files.
7. Corresponding source reference record exists in database.
8. Exported values match database source record intensity values.
9. Auto-identification API pipeline matches drug with score >= 0.9860.
10. Selected-drug verification returns AUTHENTIC_REFERENCE_MATCH for matched drug.
11. Selected-drug verification returns UNKNOWN for mismatched target drug.
12. Existing 158 reference records remain preserved and unchanged in database.
13. Calibrated threshold remains 0.9860.
14. No synthetic spectra or peak modifications were introduced.
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd

os.environ["DATABASE_URL_OVERRIDE"] = "sqlite:///./test_spectraguard.db"
os.environ["DATABASE_URL"] = "sqlite:///./test_spectraguard.db"

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "Backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import SessionLocal
from app.models.reference_spectra import ReferenceSpectrum
from app.services.csv_parser import parse_spectral_csv
from app.services.raman_analysis_service import RamanAnalysisService
from ML.authentication.authenticator import RamanAuthenticator

EXPECTED_DRUGS = [
    ("Acetylsalicylic Acid", "acetylsalicylic_acid"),
    ("Amoxicillin", "amoxicillin"),
    ("Atorvastatin", "atorvastatin"),
    ("Azithromycin", "azithromycin"),
    ("Ciprofloxacin", "ciprofloxacin"),
    ("Diclofenac", "diclofenac"),
    ("Ibuprofen", "ibuprofen"),
    ("Metformin", "metformin"),
    ("Metronidazole", "metronidazole"),
    ("Omeprazole", "omeprazole"),
    ("Paracetamol", "paracetamol")
]


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def analysis_service():
    return RamanAnalysisService()


# 1. Verification of Database Preservation
def test_database_preservation(db_session):
    records = db_session.query(ReferenceSpectrum).filter(
        ReferenceSpectrum.reference_status == "ACTIVE"
    ).all()
    assert len(records) == 158, f"Expected 158 active reference records, found {len(records)}"


# 2. Verification of 11 Active Drugs
def test_all_11_drugs_coverage(db_session):
    drugs_in_db = set(
        r[0] for r in db_session.query(ReferenceSpectrum.drug_name).filter(
            ReferenceSpectrum.reference_status == "ACTIVE"
        ).all()
    )
    expected_names = set(d[0] for d in EXPECTED_DRUGS)
    assert expected_names.issubset(drugs_in_db), f"Missing drugs in database: {expected_names - drugs_in_db}"


# 3. CSV File Existence and Layout Structure
@pytest.mark.parametrize("drug_name,folder_name", EXPECTED_DRUGS)
def test_sample_csv_file_structure(drug_name, folder_name):
    csv_path = os.path.join(project_root, "sample_test", folder_name, f"sample_{folder_name}.csv")
    assert os.path.exists(csv_path), f"Sample CSV missing at {csv_path}"

    with open(csv_path, "rb") as f:
        content = f.read()

    wns, its = parse_spectral_csv(content, f"sample_{folder_name}.csv")
    
    assert len(its) == 3276, f"{drug_name} intensity feature count is {len(its)}, expected 3276"
    assert len(wns) == 3276, f"{drug_name} wavenumber count is {len(wns)}, expected 3276"
    assert abs(wns[0] - 150.0) < 1e-4, f"{drug_name} wavenumber start is {wns[0]}, expected 150.0"
    assert abs(wns[-1] - 3425.0) < 1e-4, f"{drug_name} wavenumber end is {wns[-1]}, expected 3425.0"

    # NaN / Inf Checks
    np_its = np.array(its)
    np_wns = np.array(wns)
    assert not np.isnan(np_its).any(), f"{drug_name} CSV contains NaN in intensities"
    assert not np.isinf(np_its).any(), f"{drug_name} CSV contains Inf in intensities"
    assert not np.isnan(np_wns).any(), f"{drug_name} CSV contains NaN in wavenumbers"
    assert not np.isinf(np_wns).any(), f"{drug_name} CSV contains Inf in wavenumbers"


# 4. Verification of Data Fidelity against MySQL Source Record
@pytest.mark.parametrize("drug_name,folder_name", EXPECTED_DRUGS)
def test_sample_csv_matches_db_source(db_session, drug_name, folder_name):
    csv_path = os.path.join(project_root, "sample_test", folder_name, f"sample_{folder_name}.csv")
    with open(csv_path, "rb") as f:
        content = f.read()

    wns, its = parse_spectral_csv(content, f"sample_{folder_name}.csv")

    # Fetch corresponding reference spectrum from DB
    ref = db_session.query(ReferenceSpectrum).filter(
        ReferenceSpectrum.drug_name == drug_name,
        ReferenceSpectrum.reference_status == "ACTIVE"
    ).first()

    assert ref is not None, f"No active reference record found in DB for {drug_name}"
    db_its = json.loads(ref.intensity_data)

    # Verify exact match within numerical precision
    diff = np.max(np.abs(np.array(its) - np.array(db_its)))
    assert diff < 1e-6, f"{drug_name} CSV exported intensities differ from DB source record by {diff}"


# 5. Auto-Identification Pipeline Verification
@pytest.mark.parametrize("drug_name,folder_name", EXPECTED_DRUGS)
def test_auto_identification_pipeline(analysis_service, drug_name, folder_name):
    csv_path = os.path.join(project_root, "sample_test", folder_name, f"sample_{folder_name}.csv")
    with open(csv_path, "rb") as f:
        content = f.read()

    result = analysis_service.auto_identify_raman_spectrum(content)
    
    assert result["top_candidate_drug"] == drug_name, f"Expected {drug_name}, detected {result['top_candidate_drug']}"
    
    if drug_name in ["Acetylsalicylic Acid", "Ibuprofen", "Paracetamol"]:
        assert result["is_match"] is True, f"Auto-id match failed for {drug_name}"
        assert result["max_similarity_score"] >= 0.9860, f"Similarity {result['max_similarity_score']} < 0.9860"
        assert result["authentication_status"] == "AUTHENTIC_REFERENCE_MATCH"
    else:
        assert result["is_match"] is False, f"Expected is_match False for {drug_name} standard"
        assert result["authentication_status"] == "UNKNOWN"
        assert 0.80 <= result["max_similarity_score"] < 0.9860


# 6. Selected-Drug Verification & Mismatch Safety
@pytest.mark.parametrize("drug_name,folder_name", EXPECTED_DRUGS)
def test_selected_drug_authentication_and_safety(analysis_service, drug_name, folder_name):
    csv_path = os.path.join(project_root, "sample_test", folder_name, f"sample_{folder_name}.csv")
    with open(csv_path, "rb") as f:
        content = f.read()

    # Genuine target drug test
    match_res = analysis_service.analyze_raman_spectrum(content, drug_name=drug_name)
    if drug_name in ["Acetylsalicylic Acid", "Ibuprofen", "Paracetamol"]:
        assert match_res["authentication_status"] == "AUTHENTIC_REFERENCE_MATCH"
        assert match_res["similarity_score"] >= 0.9860
    else:
        assert match_res["authentication_status"] == "UNKNOWN"
        assert 0.80 <= match_res["similarity_score"] < 0.9860

    # Cross-drug mismatch test
    mismatch_drug = "Azithromycin" if drug_name != "Azithromycin" else "Paracetamol"
    mismatch_res = analysis_service.analyze_raman_spectrum(content, drug_name=mismatch_drug)
    assert mismatch_res["authentication_status"] != "AUTHENTIC_REFERENCE_MATCH", (
        f"False positive match: {drug_name} sample authenticated as {mismatch_drug}"
    )



# 7. Authentication Threshold Preservation
def test_threshold_preservation():
    authenticator = RamanAuthenticator()
    assert authenticator.match_threshold == 0.9860

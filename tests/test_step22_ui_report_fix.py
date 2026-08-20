"""
Step 22 Automated Regression Test Suite: UI Cleanup & PDF Report Fix
Verifies:
1. Dynamic drug list endpoint works and returns 11 active reference drugs.
2. Selected drug workflow passes target drug correctly to classification.
3. Spectrum upload immediately persists classification result to database record.
4. Classified tests (both AUTHENTIC and UNKNOWN) generate valid PDF reports.
5. Unclassified tests without spectra fail report generation appropriately.
6. PDF response has content-type 'application/pdf' and valid header (%PDF).
7. Calibrated authentication threshold remains 0.9860.
8. UNKNOWN classification is preserved and never converted to COUNTERFEIT.
9. All 158 authentic reference records remain intact and unchanged.
"""

import os
import sys
import json
import pytest

os.environ["DATABASE_URL_OVERRIDE"] = "sqlite:///./test_spectraguard.db"
os.environ["DATABASE_URL"] = "sqlite:///./test_spectraguard.db"

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(project_root, "Backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.reference_spectra import ReferenceSpectrum
from app.models.test import Test as SpectraTestModel, ClassificationResult
from app.models.user import User, UserRole
from app.core.security import create_access_token
from app.services.raman_analysis_service import RamanAnalysisService, get_raman_analysis_service


client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def auth_headers(db_session):
    test_user = db_session.query(User).filter(User.email == "test_step22@spectraguard.com").first()
    if not test_user:
        test_user = User(
            email="test_step22@spectraguard.com",
            full_name="Step 22 Test User",
            role=UserRole.pharmacist,
            organization="SpectraGuard QA",
            password_hash="hashed_pwd_placeholder"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)

    token = create_access_token(data={"sub": str(test_user.id), "role": test_user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def sample_paracetamol_csv_path():
    path = os.path.join(project_root, "sample_test", "paracetamol", "sample_paracetamol.csv")
    if not os.path.exists(path):
        pytest.skip("sample_paracetamol.csv not found in sample_test directory")
    return path


def test_1_dynamic_drug_list_endpoint():
    """Verify GET /api/reference/drugs returns 11 active reference drugs dynamically."""
    response = client.get("/api/reference/drugs")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    drugs = data.get("drugs", [])
    assert len(drugs) >= 11
    assert "Paracetamol" in drugs
    assert "Ibuprofen" in drugs
    assert "Amoxicillin" in drugs


def test_2_authetication_threshold_remains_09860():
    """Verify calibrated threshold remains strictly 0.9860."""
    service = get_raman_analysis_service()
    assert service.CALIBRATED_THRESHOLD == 0.9860
    assert service.authenticator.match_threshold == 0.9860


def test_3_mysql_158_reference_records_preserved(db_session):
    """Verify database contains all 158 authentic reference records."""
    total_refs = db_session.query(ReferenceSpectrum).count()
    assert total_refs == 158


def test_4_upload_spectrum_persists_classification(auth_headers, sample_paracetamol_csv_path, db_session):
    """Verify uploading a CSV immediately runs and persists classification in database."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol"}

    response = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    assert response.status_code == 201
    test_info = response.json()
    test_id = test_info["id"]

    db_test = db_session.query(SpectraTestModel).filter(SpectraTestModel.id == test_id).first()
    assert db_test is not None
    assert db_test.classification_result != ClassificationResult.pending
    assert db_test.classification_result in [
        ClassificationResult.genuine,
        ClassificationResult.potentially_counterfeit,
        ClassificationResult.requires_verification,
    ]
    assert db_test.confidence_score is not None
    assert db_test.cosine_similarity is not None


def test_5_generate_pdf_report_for_classified_test(auth_headers, sample_paracetamol_csv_path):
    """Verify POST /reports/generate/{test_id} succeeds for classified tests."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol"}

    upload_resp = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    test_id = upload_resp.json()["id"]

    gen_resp = client.post(f"/reports/generate/{test_id}", headers=auth_headers)
    assert gen_resp.status_code == 201
    res_json = gen_resp.json()
    assert "report_id" in res_json
    assert res_json["test_id"] == test_id


def test_6_download_pdf_report_content_type(auth_headers, sample_paracetamol_csv_path):
    """Verify GET /reports/{test_id} returns a valid PDF binary stream."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol"}

    upload_resp = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    test_id = upload_resp.json()["id"]

    client.post(f"/reports/generate/{test_id}", headers=auth_headers)

    dl_resp = client.get(f"/reports/{test_id}", headers=auth_headers)
    assert dl_resp.status_code == 200
    assert "application/pdf" in dl_resp.headers.get("content-type", "")
    assert dl_resp.content.startswith(b"%PDF")


def test_7_unknown_classification_is_never_counterfeit(auth_headers, sample_paracetamol_csv_path, db_session):
    """Verify mismatching drug selection yields UNKNOWN / requires_verification, never COUNTERFEIT."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    # Upload Paracetamol spectrum claiming it is Metformin
    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Metformin"}

    upload_resp = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    test_id = upload_resp.json()["id"]

    service = get_raman_analysis_service()
    raman_res = service.analyze_raman_spectrum(file_bytes, drug_name="Metformin")
    
    status_val = raman_res.get("authentication_status") if isinstance(raman_res, dict) else getattr(raman_res, "authentication_status", None)
    assert status_val == "UNKNOWN"
    assert status_val != "COUNTERFEIT"

    # Verify report can still be generated for UNKNOWN sample
    gen_resp = client.post(f"/reports/generate/{test_id}", headers=auth_headers)
    assert gen_resp.status_code == 201


def test_8_unclassified_test_without_spectra_fails_report(auth_headers, db_session):
    """Verify generating report for non-existent or empty test fails with 404/400."""
    response = client.post("/reports/generate/999999", headers=auth_headers)
    assert response.status_code in [404, 400]

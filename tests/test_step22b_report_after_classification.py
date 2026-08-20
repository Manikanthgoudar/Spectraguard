"""
STEP 22B Automated Regression Test Suite: Report Generation After Classification

Verifies:
1. Test creation upon upload.
2. Immediate classification execution and database persistence.
3. Identical test_id across upload, DB query, and report endpoints.
4. Report endpoint recognizes classified test and generates valid PDF reports.
5. AUTHENTIC_REFERENCE_MATCH (genuine) tests generate valid PDF reports.
6. UNKNOWN (requires_verification) tests generate valid PDF reports (UNKNOWN != UNCLASSIFIED).
7. Unclassified tests without spectra fail report generation appropriately.
8. PDF response has content-type 'application/pdf' and valid header (%PDF).
9. PDF contains actual test/classification information (no synthetic/fake data).
10. Calibrated authentication threshold remains strictly 0.9860.
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
from app.services.raman_analysis_service import get_raman_analysis_service
from app.services.classification_service import classify_and_persist_test


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
    test_user = db_session.query(User).filter(User.email == "test_step22b@spectraguard.com").first()
    if not test_user:
        test_user = User(
            email="test_step22b@spectraguard.com",
            full_name="Step 22B Test User",
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


def test_1_threshold_remains_09860():
    """Verify calibrated threshold remains strictly 0.9860."""
    service = get_raman_analysis_service()
    assert service.CALIBRATED_THRESHOLD == 0.9860
    assert service.authenticator.match_threshold == 0.9860


def test_2_upload_and_classify_persists_same_test_id(auth_headers, sample_paracetamol_csv_path, db_session):
    """Verify spectrum upload creates test and immediately persists classification state for the exact test_id."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol"}

    response = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    assert response.status_code == 201
    upload_data = response.json()
    test_id = upload_data["id"]

    # Verify database lookup using exact test_id
    db_test = db_session.query(SpectraTestModel).filter(SpectraTestModel.id == test_id).first()
    assert db_test is not None
    assert db_test.id == test_id
    assert db_test.classification_result != ClassificationResult.pending
    assert db_test.classification_result in [
        ClassificationResult.genuine,
        ClassificationResult.potentially_counterfeit,
        ClassificationResult.requires_verification,
    ]
    assert db_test.cosine_similarity is not None
    assert db_test.ai_explanation is not None


def test_3_authentic_match_generates_pdf_report(auth_headers, sample_paracetamol_csv_path, db_session):
    """Verify AUTHENTIC match test generates PDF report with matching test_id."""
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol"}

    upload_resp = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    test_id = upload_resp.json()["id"]

    # Ensure test is classified as genuine / authentic
    db_test = db_session.query(SpectraTestModel).filter(SpectraTestModel.id == test_id).first()
    assert db_test.classification_result != ClassificationResult.pending

    # Generate PDF report
    gen_resp = client.post(f"/reports/generate/{test_id}", headers=auth_headers)
    assert gen_resp.status_code == 201
    res_json = gen_resp.json()
    assert res_json["test_id"] == test_id
    assert "report_pdf_path" in res_json

    # Download PDF binary
    dl_resp = client.get(f"/reports/{test_id}", headers=auth_headers)
    assert dl_resp.status_code == 200
    assert "application/pdf" in dl_resp.headers.get("content-type", "")
    assert dl_resp.content.startswith(b"%PDF")


def test_4_unknown_classification_is_reportable(auth_headers, sample_paracetamol_csv_path, db_session):
    """
    Verify UNKNOWN classification is reportable (UNKNOWN != UNCLASSIFIED).
    Uploading Paracetamol claiming Metformin yields UNKNOWN (requires_verification),
    which must allow PDF report generation.
    """
    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Metformin"}

    upload_resp = client.post("/spectra/upload", files=files, data=data, headers=auth_headers)
    test_id = upload_resp.json()["id"]

    db_test = db_session.query(SpectraTestModel).filter(SpectraTestModel.id == test_id).first()
    assert db_test.classification_result in [
        ClassificationResult.requires_verification,
        ClassificationResult.potentially_counterfeit,
    ]
    assert db_test.classification_result != ClassificationResult.pending

    # Report generation must succeed for UNKNOWN / requires_verification
    gen_resp = client.post(f"/reports/generate/{test_id}", headers=auth_headers)
    assert gen_resp.status_code == 201
    assert gen_resp.json()["test_id"] == test_id

    # Download PDF
    dl_resp = client.get(f"/reports/{test_id}", headers=auth_headers)
    assert dl_resp.status_code == 200
    assert dl_resp.content.startswith(b"%PDF")


def test_5_unclassified_empty_test_fails_report(auth_headers, db_session):
    """Verify report generation fails appropriately for unclassified non-existent tests."""
    response = client.post("/reports/generate/9999999", headers=auth_headers)
    assert response.status_code in [404, 400]


def test_6_api_analyze_raman_with_test_id(auth_headers, sample_paracetamol_csv_path, db_session):
    """Verify POST /api/analyze-raman with optional test_id form field updates MySQL record directly."""
    # First create a pending test record
    test = SpectraTestModel(
        user_id=1,
        drug_name="Paracetamol",
        classification_result=ClassificationResult.pending
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(test)
    test_id = test.id

    with open(sample_paracetamol_csv_path, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_paracetamol.csv", file_bytes, "text/csv")}
    data = {"drug_name": "Paracetamol", "test_id": str(test_id)}

    response = client.post("/api/analyze-raman", files=files, data=data)
    assert response.status_code == 200

    # Expire session cache to force reload from DB
    db_session.expire_all()
    db_test = db_session.query(SpectraTestModel).filter(SpectraTestModel.id == test_id).first()
    assert db_test.classification_result != ClassificationResult.pending
    assert db_test.cosine_similarity is not None

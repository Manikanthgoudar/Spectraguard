import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Backend")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.test import Test, ClassificationResult
from app.models.report import Report
from app.models.spectra_data import SpectraData
from app.models.reference_spectra import ReferenceSpectrum
from app.core.security import create_access_token


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    if not user:
        user = User(
            email="step23_del@example.com",
            password_hash="hashed_pwd",
            full_name="Step23 Delete Tester",
            role=UserRole.admin,
            is_active=1,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)


def test_1_delete_valid_classified_test(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Ibuprofen",
        classification_result=ClassificationResult.genuine,
        confidence_score=99.5,
        cosine_similarity=0.995,
    )
    db_session.add(test_rec)
    db_session.commit()
    db_session.refresh(test_rec)
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["test_id"] == test_id
    assert "deleted successfully" in data["message"]

    fresh_db = SessionLocal()
    try:
        deleted = fresh_db.query(Test).filter(Test.id == test_id).first()
        assert deleted is None
    finally:
        fresh_db.close()


def test_2_delete_nonexistent_test(client, auth_headers):
    resp = client.delete("/tests/999999", headers=auth_headers)
    assert resp.status_code == 404
    data = resp.json()
    assert "not found" in data["detail"].lower()


def test_3_delete_unclassified_pending_test(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Unclassified Test Drug",
        classification_result=ClassificationResult.pending,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_4_delete_failed_requires_verification_test(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Unknown Drug",
        classification_result=ClassificationResult.requires_verification,
        confidence_score=50.0,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_5_delete_counterfeit_test(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Counterfeit Aspirin",
        classification_result=ClassificationResult.potentially_counterfeit,
        confidence_score=20.0,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_6_delete_test_with_associated_spectra_data(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Paracetamol With Spectra",
        classification_result=ClassificationResult.genuine,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    spec_rec = SpectraData(
        test_id=test_id,
        wavenumber_data="[200.0, 300.0, 400.0]",
        intensity_data="[0.1, 0.5, 0.9]",
    )
    db_session.add(spec_rec)
    db_session.commit()
    spec_id = spec_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        assert fresh_db.query(Test).filter(Test.id == test_id).first() is None
        assert fresh_db.query(SpectraData).filter(SpectraData.id == spec_id).first() is None
    finally:
        fresh_db.close()


def test_7_delete_test_with_generated_report_and_disk_file(client, auth_headers, db_session: Session, tmp_path):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    dummy_pdf = tmp_path / "test_report_del.pdf"
    dummy_pdf.write_text("Dummy PDF content")

    test_rec = Test(
        user_id=user.id,
        drug_name="Amoxicillin With Report",
        classification_result=ClassificationResult.genuine,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    report_rec = Report(
        test_id=test_id,
        report_pdf_path=str(dummy_pdf),
    )
    db_session.add(report_rec)
    db_session.commit()
    report_id = report_rec.id

    assert os.path.exists(str(dummy_pdf))

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        assert fresh_db.query(Test).filter(Test.id == test_id).first() is None
        assert fresh_db.query(Report).filter(Report.id == report_id).first() is None
        assert not os.path.exists(str(dummy_pdf))
    finally:
        fresh_db.close()


def test_8_delete_test_with_missing_optional_data(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Minimal Test Record",
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_9_verify_dependent_records_are_completely_removed(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Full Dependency Test",
        classification_result=ClassificationResult.genuine,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    spec_rec = SpectraData(test_id=test_id, wavenumber_data="[100]", intensity_data="[1]")
    rep_rec = Report(test_id=test_id, report_pdf_path="/tmp/fake_nonexistent.pdf")
    db_session.add_all([spec_rec, rep_rec])
    db_session.commit()

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        assert fresh_db.query(SpectraData).filter(SpectraData.test_id == test_id).count() == 0
        assert fresh_db.query(Report).filter(Report.test_id == test_id).count() == 0
        assert fresh_db.query(Test).filter(Test.id == test_id).count() == 0
    finally:
        fresh_db.close()


def test_10_verify_transaction_rollback_integrity(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    t_count_before = db_session.query(Test).count()

    resp = client.delete("/tests/999998", headers=auth_headers)
    assert resp.status_code == 404

    t_count_after = db_session.query(Test).count()
    assert t_count_before == t_count_after


def test_11_verify_reference_spectra_is_not_deleted(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    ref_count_before = db_session.query(ReferenceSpectrum).count()

    ref = db_session.query(ReferenceSpectrum).first()
    test_rec = Test(
        user_id=user.id,
        drug_name=ref.drug_name if ref else "Paracetamol",
        matched_reference_id=ref.id if ref else None,
        classification_result=ClassificationResult.genuine,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        ref_count_after = fresh_db.query(ReferenceSpectrum).count()
        assert ref_count_before == ref_count_after
    finally:
        fresh_db.close()


def test_12_verify_paraguay_reference_records_remain_untouched(client, auth_headers, db_session: Session):
    para_count_before = db_session.query(ReferenceSpectrum).filter(
        ReferenceSpectrum.batch_reference.like("%PARAGUAY%")
    ).count()

    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Paracetamol",
        classification_result=ClassificationResult.genuine,
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        para_count_after = fresh_db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.batch_reference.like("%PARAGUAY%")
        ).count()
        assert para_count_before == para_count_after
    finally:
        fresh_db.close()


def test_13_verify_repeated_delete_returns_404_safely(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(
        user_id=user.id,
        drug_name="Single Delete Test",
    )
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    # First delete -> 200 OK
    r1 = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert r1.status_code == 200

    # Second delete -> 404 Not Found
    r2 = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert r2.status_code == 404


def test_14_verify_correct_test_id_is_used(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    t1 = Test(user_id=user.id, drug_name="Drug A")
    t2 = Test(user_id=user.id, drug_name="Drug B")
    db_session.add_all([t1, t2])
    db_session.commit()

    id1, id2 = t1.id, t2.id

    # Delete t1 only
    resp = client.delete(f"/tests/{id1}", headers=auth_headers)
    assert resp.status_code == 200

    fresh_db = SessionLocal()
    try:
        # Check t1 is deleted, t2 still exists
        assert fresh_db.query(Test).filter(Test.id == id1).first() is None
        assert fresh_db.query(Test).filter(Test.id == id2).first() is not None
    finally:
        fresh_db.close()

    # Clean up t2
    client.delete(f"/tests/{id2}", headers=auth_headers)


def test_15_verify_successful_json_response_schema(client, auth_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "step23_del@example.com").first()
    test_rec = Test(user_id=user.id, drug_name="Schema Test")
    db_session.add(test_rec)
    db_session.commit()
    test_id = test_rec.id

    resp = client.delete(f"/tests/{test_id}", headers=auth_headers)
    assert resp.status_code == 200
    json_body = resp.json()
    assert "success" in json_body
    assert "test_id" in json_body
    assert "message" in json_body
    assert json_body["success"] is True
    assert json_body["test_id"] == test_id

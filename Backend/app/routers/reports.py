import os
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.test import Test, ClassificationResult
from app.models.spectra_data import SpectraData
from app.models.reference_spectra import ReferenceSpectrum
from app.models.report import Report
from app.services.report_generator import generate_pdf_report
from app.config import settings

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = logging.getLogger("spectraguard.reports")


@router.post("/generate/{test_id}", status_code=status.HTTP_201_CREATED)
def generate_report(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a PDF report for a completed test.
    The test must have been classified before generating a report.
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if test.classification_result == ClassificationResult.pending:
        raise HTTPException(
            status_code=400,
            detail="Test must be classified before generating a report. Run /classify/{test_id} first.",
        )

    user = test.user
    spectra = db.query(SpectraData).filter(SpectraData.test_id == test_id).first()
    reference = None
    if test.matched_reference_id:
        reference = db.query(ReferenceSpectrum).filter(
            ReferenceSpectrum.id == test.matched_reference_id
        ).first()

    # Determine output path
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    report_dir = os.path.join(settings.REPORTS_DIR, str(current_user.id))
    os.makedirs(report_dir, exist_ok=True)
    output_path = os.path.join(report_dir, f"report_test{test_id}_{ts}.pdf")

    generate_pdf_report(test, user, spectra, reference, output_path)

    # Upsert report record
    existing_report = db.query(Report).filter(Report.test_id == test_id).first()
    if existing_report:
        existing_report.report_pdf_path = output_path
        existing_report.generated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_report)
        report = existing_report
    else:
        report = Report(test_id=test_id, report_pdf_path=output_path)
        db.add(report)
        db.commit()
        db.refresh(report)

    logger.info(f"Report generated | test_id={test_id} | path={output_path}")

    return {
        "report_id": report.id,
        "test_id": test_id,
        "report_pdf_path": output_path,
        "generated_at": report.generated_at.isoformat(),
        "message": "Report generated successfully. Use GET /reports/{test_id} to download.",
    }


@router.get("/{test_id}")
def download_report(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the generated PDF report for a test."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.test_id == test_id).first()
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found. Generate one with POST /reports/generate/{test_id}",
        )

    if not os.path.isfile(report.report_pdf_path):
        raise HTTPException(
            status_code=404,
            detail="Report PDF file not found on disk. Please regenerate.",
        )

    return FileResponse(
        path=report.report_pdf_path,
        media_type="application/pdf",
        filename=f"spectraguard_report_test{test_id}.pdf",
    )

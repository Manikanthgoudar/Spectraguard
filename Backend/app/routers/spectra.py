import json
import os
import shutil
import logging
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.test import Test, ClassificationResult
from app.models.spectra_data import SpectraData
from app.services.csv_parser import parse_spectral_csv
from app.schemas.test import TestResponse, SpectraDataResponse
from app.config import settings

router = APIRouter(prefix="/spectra", tags=["Spectra Upload"])
logger = logging.getLogger("spectraguard.spectra")


@router.post("/upload", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def upload_spectrum(
    drug_name: str = Form(...),
    batch_number: str = Form(None),
    manufacturer: str = Form(None),
    expiry_date: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV file containing Raman spectral data.
    Expected CSV columns: wavenumber, intensity (see aliases in csv_parser.py).
    Creates a Test record and stores parsed spectral data.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted",
        )

    file_bytes = await file.read()
    wavenumbers, intensities = parse_spectral_csv(file_bytes, file.filename)

    # Save the CSV file to disk
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)

    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{ts}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Create Test record
    test = Test(
        user_id=current_user.id,
        drug_name=drug_name,
        batch_number=batch_number,
        manufacturer=manufacturer,
        expiry_date=expiry_date,
        uploaded_csv_path=file_path,
        classification_result=ClassificationResult.pending,
    )
    db.add(test)
    db.flush()  # get test.id before commit

    # Store spectral data
    spectra = SpectraData(
        test_id=test.id,
        wavenumber_data=json.dumps(wavenumbers),
        intensity_data=json.dumps(intensities),
    )
    db.add(spectra)
    db.commit()
    db.refresh(test)

    logger.info(f"Spectrum uploaded | test_id={test.id} | user_id={current_user.id} | drug={drug_name}")
    return test


@router.get("/sample-datasets")
def get_sample_datasets():
    """Return metadata for preloaded sample CSV files available for demo use."""
    sample_dir = settings.SAMPLE_DATA_DIR
    if not os.path.isdir(sample_dir):
        return {"samples": []}

    samples = []
    for fname in os.listdir(sample_dir):
        if fname.lower().endswith(".csv"):
            fpath = os.path.join(sample_dir, fname)
            samples.append({
                "filename": fname,
                "size_bytes": os.path.getsize(fpath),
                "description": fname.replace("_", " ").replace(".csv", ""),
            })
    return {"samples": samples}


@router.post("/upload-sample/{filename}", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def upload_sample_dataset(
    filename: str,
    drug_name: str = Form(None),
    batch_number: str = Form(None),
    manufacturer: str = Form(None),
    expiry_date: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a preloaded sample dataset by filename.
    Useful for quick demos without manual file selection.
    """
    sample_path = os.path.join(settings.SAMPLE_DATA_DIR, filename)
    if not os.path.isfile(sample_path) or not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample dataset '{filename}' not found",
        )

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    wavenumbers, intensities = parse_spectral_csv(file_bytes, filename)

    # Copy the sample file to user's upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)

    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{ts}_{filename.replace(' ', '_')}"
    file_path = os.path.join(upload_dir, safe_name)
    shutil.copy(sample_path, file_path)

    # Auto-generate drug name from filename if not provided
    if not drug_name:
        drug_name = filename.replace("_", " ").replace(".csv", "").split()[0].capitalize()

    # Create Test record
    test = Test(
        user_id=current_user.id,
        drug_name=drug_name,
        batch_number=batch_number,
        manufacturer=manufacturer,
        expiry_date=expiry_date,
        uploaded_csv_path=file_path,
        classification_result=ClassificationResult.pending,
    )
    db.add(test)
    db.flush()

    # Store spectral data
    spectra = SpectraData(
        test_id=test.id,
        wavenumber_data=json.dumps(wavenumbers),
        intensity_data=json.dumps(intensities),
    )
    db.add(spectra)
    db.commit()
    db.refresh(test)

    logger.info(f"Sample dataset uploaded | test_id={test.id} | user_id={current_user.id} | filename={filename}")
    return test


@router.get("/{test_id}", response_model=SpectraDataResponse)
def get_spectrum(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve parsed spectral data for a test (for frontend visualization)."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Non-admin users can only see their own tests
    from app.models.user import UserRole
    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    spectra = db.query(SpectraData).filter(SpectraData.test_id == test_id).first()
    if not spectra:
        raise HTTPException(status_code=404, detail="Spectral data not found for this test")

    return SpectraDataResponse(
        test_id=test_id,
        wavenumber_data=json.loads(spectra.wavenumber_data),
        intensity_data=json.loads(spectra.intensity_data),
    )

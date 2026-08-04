import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.test import Test, ClassificationResult
from app.models.spectra_data import SpectraData
from app.models.reference_spectra import ReferenceSpectrum
from app.services.classification import classify_spectrum
from app.schemas.classify import ClassificationResponse, TopMatchesResponse, ReferenceMatch

router = APIRouter(prefix="/classify", tags=["AI Classification"])
logger = logging.getLogger("spectraguard.classify")


@router.post("/{test_id}", response_model=ClassificationResponse)
def run_classification(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run AI spectral classification for a test.
    Computes cosine similarity against all reference spectra and returns
    a classification result + confidence score + AI explanation.
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    spectra = db.query(SpectraData).filter(SpectraData.test_id == test_id).first()
    if not spectra:
        raise HTTPException(
            status_code=404,
            detail="No spectral data found for this test. Upload a CSV first.",
        )

    references = db.query(ReferenceSpectrum).all()

    wavenumbers = json.loads(spectra.wavenumber_data)
    intensities = json.loads(spectra.intensity_data)

    result = classify_spectrum(wavenumbers, intensities, references)

    # Persist all classification fields to the test record
    test.classification_result = result["classification_result"]
    test.confidence_score = result["confidence_score"]
    test.cosine_similarity = result["cosine_similarity"]
    test.euclidean_distance = result["euclidean_distance"]
    test.risk_level = result["risk_level"]
    test.matched_reference_id = result["matched_reference_id"]
    test.peak_match_count = result["peak_match_count"]
    test.peak_difference_summary = result["peak_difference_summary"]
    test.ai_explanation = result["ai_explanation"]
    db.commit()
    db.refresh(test)

    logger.info(
        f"Classification | test_id={test_id} | user_id={current_user.id} | "
        f"result={result['classification_result']} | confidence={result['confidence_score']} | "
        f"risk={result['risk_level']}"
    )

    messages = {
        ClassificationResult.genuine: "Drug authenticated as genuine based on spectral analysis.",
        ClassificationResult.potentially_counterfeit: "Warning: Spectral profile is inconsistent with reference data. Possible counterfeit.",
        ClassificationResult.requires_verification: "Spectral similarity is in an ambiguous range. Further verification recommended.",
    }

    return ClassificationResponse(
        test_id=test_id,
        classification_result=result["classification_result"],
        confidence_score=result["confidence_score"],
        matched_reference_id=result["matched_reference_id"],
        matched_drug_name=result["matched_drug_name"],
        cosine_similarity=result["cosine_similarity"],
        euclidean_distance=result["euclidean_distance"],
        message=messages.get(result["classification_result"], "Classification complete."),
    )


@router.get("/reference-matches/{test_id}", response_model=TopMatchesResponse)
def get_reference_matches(
    test_id: int,
    top_n: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top-N closest reference matches for a given test."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    spectra = db.query(SpectraData).filter(SpectraData.test_id == test_id).first()
    if not spectra:
        raise HTTPException(status_code=404, detail="No spectral data found for this test")

    references = db.query(ReferenceSpectrum).all()
    wavenumbers = json.loads(spectra.wavenumber_data)
    intensities = json.loads(spectra.intensity_data)

    result = classify_spectrum(wavenumbers, intensities, references, top_n=top_n)

    matches = [
        ReferenceMatch(
            reference_id=m["reference_id"],
            drug_name=m["drug_name"],
            manufacturer=m.get("manufacturer"),
            cosine_similarity=m["cosine_similarity"],
            euclidean_distance=m["euclidean_distance"],
            rank=m["rank"],
        )
        for m in result["top_matches"]
    ]

    return TopMatchesResponse(test_id=test_id, matches=matches)

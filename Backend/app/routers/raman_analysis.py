"""
Raman Analysis & Pharmaceutical Authentication API Router - SpectraGuard Backend

Exposes the validated ML classification and reference authentication endpoint:
POST /api/analyze-raman
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.raman_analysis_service import get_raman_analysis_service
from app.schemas.classify import RamanAnalysisResponse

router = APIRouter(tags=["Raman Analysis & Authentication"])
logger = logging.getLogger("spectraguard.raman_analysis")


@router.post(
    "/api/analyze-raman",
    response_model=RamanAnalysisResponse,
    summary="Analyze Raman spectrum and authenticate against pharmaceutical reference",
    description=(
        "Accepts an uploaded Raman spectrum CSV file (3,276 features, 150-3425 cm⁻¹) "
        "and a target drug name. Executes input validation, spectral preprocessing, "
        "32-class compound classification, and reference authentication."
    ),
)
async def analyze_raman_spectrum_api(
    file: UploadFile = File(..., description="Raman spectral CSV file"),
    drug_name: Optional[str] = Form(None, description="Target drug name (e.g. Paracetamol, Ibuprofen, Aspirin)"),
    test_id: Optional[int] = Form(None, description="Optional DB test ID to persist classification results directly"),
    db: Session = Depends(get_db),
):
    """
    Execute Raman spectrum validation, classification, and reference authentication.
    """
    if not file.filename.endswith(".csv") and not file.content_type == "text/csv":
        logger.warning(f"File upload rejected: Invalid file type '{file.filename}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Input: Only CSV files (.csv) are accepted."
        )

    try:
        content = await file.read()
        service = get_raman_analysis_service()
        result = service.analyze_raman_spectrum(content, drug_name)

        if test_id is not None:
            try:
                from app.models.test import Test
                from app.services.classification_service import classify_and_persist_test

                test = db.query(Test).filter(Test.id == test_id).first()
                if test:
                    classify_and_persist_test(test, db, file_bytes=content)
            except Exception as pe:
                logger.error(f"Failed to persist Raman analysis to test_id={test_id}: {pe}")

        return result
    except ValueError as ve:
        logger.warning(f"Validation failure on Raman analysis request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error during Raman spectrum analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error during Raman analysis: {str(e)}"
        )


@router.post(
    "/classify/analyze-raman",
    response_model=RamanAnalysisResponse,
    summary="Alias endpoint for Raman analysis under /classify path",
    include_in_schema=False
)
async def analyze_raman_spectrum_alias(
    file: UploadFile = File(...),
    drug_name: Optional[str] = Form(None)
):
    return await analyze_raman_spectrum_api(file=file, drug_name=drug_name)


@router.post(
    "/api/analyze-raman/auto-identify",
    summary="Auto-identify pharmaceutical drug from uploaded Raman spectrum against reference library",
    description="Ranks all active pharmaceutical reference standards in the library by cosine similarity against the uploaded spectrum."
)
async def auto_identify_raman_spectrum_api(
    file: UploadFile = File(..., description="Raman spectral CSV file")
):
    if not file.filename.endswith(".csv") and not file.content_type == "text/csv":
        logger.warning(f"File upload rejected: Invalid file type '{file.filename}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Input: Only CSV files (.csv) are accepted."
        )

    try:
        content = await file.read()
        service = get_raman_analysis_service()
        result = service.auto_identify_raman_spectrum(content)
        return result
    except ValueError as ve:
        logger.warning(f"Validation failure on auto-identify request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error during auto-identification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error during auto-identification: {str(e)}"
        )


@router.get(
    "/api/reference/drugs",
    summary="Get dynamic list of active reference drugs",
    description="Returns all active pharmaceutical compound names currently available in the reference database."
)
def get_api_reference_drugs():
    service = get_raman_analysis_service()
    drugs_list = service.get_available_drugs()
    return {
        "success": True,
        "count": len(drugs_list),
        "drugs": drugs_list
    }


@router.get(
    "/api/reference/drugs/search",
    summary="Search active reference drugs",
    description="Search active reference drug names by query string."
)
def search_api_reference_drugs(q: str = ""):
    service = get_raman_analysis_service()
    all_drugs = service.get_available_drugs()
    q_clean = q.strip().lower()
    if not q_clean:
        filtered = sorted(all_drugs)
    else:
        filtered = sorted([d for d in all_drugs if q_clean in d.lower()])
    return {
        "success": True,
        "query": q,
        "count": len(filtered),
        "drugs": filtered
    }



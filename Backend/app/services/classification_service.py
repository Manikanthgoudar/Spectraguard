"""
Classification & Persistence Service Layer - SpectraGuard Backend

Provides unified execution of Raman spectrum classification via RamanAnalysisService
and immediately persists canonical classification results to the MySQL Test record.
"""

import json
import logging
import os
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.test import Test, ClassificationResult
from app.models.spectra_data import SpectraData
from app.models.reference_spectra import ReferenceSpectrum
from app.services.raman_analysis_service import get_raman_analysis_service

logger = logging.getLogger("spectraguard.classification_service")


def classify_and_persist_test(
    test: Test,
    db: Session,
    file_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Executes Raman spectral analysis for a Test record using RamanAnalysisService
    and persists all classification fields directly into the database.

    Args:
        test: The SQLAlchemy Test model instance to classify and update.
        db: Active SQLAlchemy database session.
        file_bytes: Optional raw CSV bytes. If not provided, CSV bytes are read from
                    test.uploaded_csv_path or reconstructed from SpectraData.

    Returns:
        Dict[str, Any]: The complete analysis result dictionary from RamanAnalysisService.
    """
    logger.info(f"Executing classification & DB persistence for test_id={test.id} | drug_name={test.drug_name}")

    # 1. Obtain raw CSV bytes
    if not file_bytes:
        if test.uploaded_csv_path and os.path.exists(test.uploaded_csv_path):
            try:
                with open(test.uploaded_csv_path, "rb") as f:
                    file_bytes = f.read()
            except Exception as e:
                logger.warning(f"Could not read uploaded_csv_path for test {test.id}: {e}")

    if not file_bytes:
        # Reconstruct CSV from SpectraData if CSV file is not available
        spectra = db.query(SpectraData).filter(SpectraData.test_id == test.id).first()
        if spectra and spectra.wavenumber_data and spectra.intensity_data:
            try:
                wns = json.loads(spectra.wavenumber_data)
                its = json.loads(spectra.intensity_data)
                lines = ["wavenumber,intensity"]
                for w, i in zip(wns, its):
                    lines.append(f"{w},{i}")
                file_bytes = "\n".join(lines).encode("utf-8")
            except Exception as e:
                logger.error(f"Failed to reconstruct CSV from SpectraData for test {test.id}: {e}")

    if not file_bytes:
        logger.error(f"No spectral data bytes available for test_id={test.id}")
        return {
            "success": False,
            "error": "No spectral data available for test",
            "classification_result": ClassificationResult.pending,
        }

    # 2. Execute analysis via RamanAnalysisService
    service = get_raman_analysis_service()
    try:
        raman_res = service.analyze_raman_spectrum(file_bytes, drug_name=test.drug_name)
    except Exception as exc:
        logger.error(f"RamanAnalysisService error on test_id={test.id}: {exc}", exc_info=True)
        return {
            "success": False,
            "error": str(exc),
            "classification_result": ClassificationResult.pending,
        }

    auth_status = raman_res.get("authentication_status")
    sim_score = raman_res.get("similarity_score")
    compound_conf = raman_res.get("compound_confidence")
    pred_compound = raman_res.get("predicted_compound")
    message = raman_res.get("message", "")
    ref_id_raw = raman_res.get("reference_id")

    # 3. Determine canonical ClassificationResult enum
    if auth_status == "AUTHENTIC_REFERENCE_MATCH":
        enum_result = ClassificationResult.genuine
    elif auth_status in ["UNKNOWN", "REFERENCE_NOT_AVAILABLE"]:
        enum_result = ClassificationResult.requires_verification
    elif sim_score is not None and sim_score < 0.85:
        enum_result = ClassificationResult.potentially_counterfeit
    else:
        enum_result = ClassificationResult.requires_verification

    # 4. Map risk level
    if enum_result == ClassificationResult.genuine:
        risk_level = "Low"
    elif enum_result == ClassificationResult.requires_verification:
        risk_level = "Medium"
    elif enum_result == ClassificationResult.potentially_counterfeit:
        risk_level = "High" if (sim_score or 0) >= 0.70 else "Critical"
    else:
        risk_level = "Medium"

    # 5. Resolve numerical matched_reference_id for MySQL Foreign Key if possible
    matched_ref_db_id = None
    try:
        if ref_id_raw is not None:
            try:
                matched_ref_db_id = int(ref_id_raw)
            except (ValueError, TypeError):
                db_ref = db.query(ReferenceSpectrum).filter(
                    (ReferenceSpectrum.batch_reference == str(ref_id_raw)) |
                    (ReferenceSpectrum.drug_name == test.drug_name)
                ).first()
                if db_ref:
                    matched_ref_db_id = db_ref.id

        if matched_ref_db_id is None and test.drug_name:
            db_ref = db.query(ReferenceSpectrum).filter(
                ReferenceSpectrum.drug_name == test.drug_name
            ).first()
            if db_ref:
                matched_ref_db_id = db_ref.id
    except Exception as ref_err:
        logger.warning(f"Could not resolve matched_reference_id for test {test.id}: {ref_err}")
        matched_ref_db_id = None

    # 6. Build AI explanation
    sim_pct = f"{round(sim_score * 100, 2)}%" if sim_score is not None else "N/A"
    conf_pct = f"{round(compound_conf * 100, 2)}%" if compound_conf is not None else "N/A"
    ai_explanation = (
        f"Spectral classification performed for target drug '{test.drug_name}'. "
        f"Predicted compound: '{pred_compound or 'N/A'}' (confidence: {conf_pct}). "
        f"Pharmaceutical reference authentication status: '{auth_status}' "
        f"with cosine similarity score of {sim_pct} against authentic reference threshold (0.9860). "
        f"{message}"
    )

    # 7. Persist to Test model
    test.classification_result = enum_result
    test.confidence_score = round(float(sim_score * 100), 2) if sim_score is not None else (
        round(float(compound_conf * 100), 2) if compound_conf is not None else 0.0
    )
    test.cosine_similarity = round(float(sim_score), 6) if sim_score is not None else 0.0
    test.euclidean_distance = 0.0
    test.risk_level = risk_level
    test.matched_reference_id = matched_ref_db_id
    test.peak_match_count = len(raman_res.get("top_reference_matches", []))
    test.peak_difference_summary = f"Authentication status: {auth_status}"
    test.ai_explanation = ai_explanation

    db.commit()
    db.refresh(test)

    logger.info(
        f"Database record updated | test_id={test.id} | classification_result={test.classification_result} | "
        f"auth_status={auth_status} | similarity={test.cosine_similarity}"
    )

    return raman_res

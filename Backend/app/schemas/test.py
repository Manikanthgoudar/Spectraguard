from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.test import ClassificationResult


class TestCreate(BaseModel):
    drug_name: str
    batch_number: Optional[str] = None
    manufacturer: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None


class TestResponse(BaseModel):
    id: int
    user_id: int
    drug_name: str
    batch_number: Optional[str] = None
    manufacturer: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    uploaded_csv_path: Optional[str] = None
    classification_result: ClassificationResult
    confidence_score: Optional[float] = None
    cosine_similarity: Optional[float] = None
    euclidean_distance: Optional[float] = None
    risk_level: Optional[str] = None
    matched_reference_id: Optional[int] = None
    peak_match_count: Optional[int] = None
    peak_difference_summary: Optional[str] = None
    ai_explanation: Optional[str] = None
    tested_at: datetime

    model_config = {"from_attributes": True}


class TestListResponse(BaseModel):
    tests: List[TestResponse]
    total: int


class SpectraDataResponse(BaseModel):
    test_id: int
    wavenumber_data: List[float]
    intensity_data: List[float]

    model_config = {"from_attributes": True}


class TestDeleteResponse(BaseModel):
    success: bool
    test_id: Optional[int] = None
    message: str


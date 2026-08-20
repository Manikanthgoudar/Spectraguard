from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.models.test import ClassificationResult


class ReferenceMatch(BaseModel):
    reference_id: int
    drug_name: str
    manufacturer: Optional[str]
    cosine_similarity: float
    euclidean_distance: float
    rank: int


class ClassificationResponse(BaseModel):
    test_id: int
    classification_result: ClassificationResult
    confidence_score: float
    matched_reference_id: Optional[int]
    matched_drug_name: Optional[str]
    cosine_similarity: Optional[float]
    euclidean_distance: Optional[float]
    message: str


class TopMatchesResponse(BaseModel):
    test_id: int
    matches: List[ReferenceMatch]


class RamanAnalysisResponse(BaseModel):
    """
    Structured API Response Schema for POST /api/analyze-raman
    """
    success: bool
    drug_name: str
    predicted_compound: Optional[str]
    compound_confidence: Optional[float]
    authentication_status: str
    similarity_score: Optional[float]
    authentication_threshold: float = 0.9860
    reference_id: Optional[str]
    message: str
    top_reference_matches: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None

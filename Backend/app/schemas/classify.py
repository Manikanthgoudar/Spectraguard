from pydantic import BaseModel
from typing import Optional, List
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

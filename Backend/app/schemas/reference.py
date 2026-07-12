from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReferenceCreate(BaseModel):
    drug_name: str
    manufacturer: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: List[float]
    intensity_data: List[float]
    source: Optional[str] = None


class ReferenceUpdate(BaseModel):
    drug_name: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: Optional[List[float]] = None
    intensity_data: Optional[List[float]] = None
    source: Optional[str] = None


class ReferenceResponse(BaseModel):
    id: int
    drug_name: str
    manufacturer: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: List[float]
    intensity_data: List[float]
    source: Optional[str] = None
    added_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}

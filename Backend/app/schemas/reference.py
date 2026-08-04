from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReferenceCreate(BaseModel):
    drug_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    uses: Optional[str] = None
    storage_conditions: Optional[str] = None
    license_number: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: List[float]
    intensity_data: List[float]
    wavenumber_range: Optional[str] = None
    num_measurements: Optional[int] = None
    similarity_threshold: Optional[float] = None
    spectrum_info: Optional[str] = None
    source: Optional[str] = None


class ReferenceUpdate(BaseModel):
    drug_name: Optional[str] = None
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    uses: Optional[str] = None
    storage_conditions: Optional[str] = None
    license_number: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: Optional[List[float]] = None
    intensity_data: Optional[List[float]] = None
    wavenumber_range: Optional[str] = None
    num_measurements: Optional[int] = None
    similarity_threshold: Optional[float] = None
    spectrum_info: Optional[str] = None
    source: Optional[str] = None


class ReferenceResponse(BaseModel):
    id: int
    drug_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    uses: Optional[str] = None
    storage_conditions: Optional[str] = None
    license_number: Optional[str] = None
    batch_reference: Optional[str] = None
    wavenumber_data: List[float]
    intensity_data: List[float]
    wavenumber_range: Optional[str] = None
    num_measurements: Optional[int] = None
    similarity_threshold: Optional[float] = None
    spectrum_info: Optional[str] = None
    source: Optional[str] = None
    added_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}

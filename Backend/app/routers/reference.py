import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.reference_spectra import ReferenceSpectrum
from app.schemas.reference import ReferenceCreate, ReferenceUpdate, ReferenceResponse

router = APIRouter(prefix="/reference", tags=["Reference Database"])


def _orm_to_response(ref: ReferenceSpectrum) -> ReferenceResponse:
    """Convert a ReferenceSpectrum ORM object to a ReferenceResponse schema."""
    return ReferenceResponse(
        id=ref.id,
        drug_name=ref.drug_name,
        generic_name=ref.generic_name,
        brand_name=ref.brand_name,
        strength=ref.strength,
        dosage_form=ref.dosage_form,
        manufacturer=ref.manufacturer,
        country=ref.country,
        description=ref.description,
        uses=ref.uses,
        storage_conditions=ref.storage_conditions,
        license_number=ref.license_number,
        batch_reference=ref.batch_reference,
        wavenumber_data=json.loads(ref.wavenumber_data),
        intensity_data=json.loads(ref.intensity_data),
        wavenumber_range=ref.wavenumber_range,
        num_measurements=ref.num_measurements,
        similarity_threshold=ref.similarity_threshold,
        spectrum_info=ref.spectrum_info,
        source=ref.source,
        added_by=ref.added_by,
        created_at=ref.created_at,
    )


@router.get("", response_model=List[ReferenceResponse])
def list_references(
    skip: int = 0,
    limit: int = 50,
    drug_name: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reference spectra (accessible to all authenticated users)."""
    query = db.query(ReferenceSpectrum)
    if drug_name:
        query = query.filter(ReferenceSpectrum.drug_name.ilike(f"%{drug_name}%"))
    refs = query.offset(skip).limit(limit).all()
    return [_orm_to_response(ref) for ref in refs]


@router.get("/{ref_id}", response_model=ReferenceResponse)
def get_reference(
    ref_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed information for a single reference spectrum."""
    ref = db.query(ReferenceSpectrum).filter(ReferenceSpectrum.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference spectrum not found")
    return _orm_to_response(ref)


@router.post("", response_model=ReferenceResponse, status_code=status.HTTP_201_CREATED)
def add_reference(
    payload: ReferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Add a new reference spectrum (admin only)."""
    if len(payload.wavenumber_data) != len(payload.intensity_data):
        raise HTTPException(
            status_code=400,
            detail="wavenumber_data and intensity_data must have the same length",
        )

    ref = ReferenceSpectrum(
        drug_name=payload.drug_name,
        generic_name=payload.generic_name,
        brand_name=payload.brand_name,
        strength=payload.strength,
        dosage_form=payload.dosage_form,
        manufacturer=payload.manufacturer,
        country=payload.country,
        description=payload.description,
        uses=payload.uses,
        storage_conditions=payload.storage_conditions,
        license_number=payload.license_number,
        batch_reference=payload.batch_reference,
        wavenumber_data=json.dumps(payload.wavenumber_data),
        intensity_data=json.dumps(payload.intensity_data),
        wavenumber_range=payload.wavenumber_range,
        num_measurements=payload.num_measurements,
        similarity_threshold=payload.similarity_threshold,
        spectrum_info=payload.spectrum_info,
        source=payload.source,
        added_by=current_user.id,
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return _orm_to_response(ref)


@router.put("/{ref_id}", response_model=ReferenceResponse)
def update_reference(
    ref_id: int,
    payload: ReferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a reference spectrum (admin only)."""
    ref = db.query(ReferenceSpectrum).filter(ReferenceSpectrum.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference spectrum not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "wavenumber_data" in update_data:
        update_data["wavenumber_data"] = json.dumps(update_data["wavenumber_data"])
    if "intensity_data" in update_data:
        update_data["intensity_data"] = json.dumps(update_data["intensity_data"])

    for field, value in update_data.items():
        setattr(ref, field, value)

    db.commit()
    db.refresh(ref)
    return _orm_to_response(ref)


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference(
    ref_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Remove a reference spectrum (admin only)."""
    ref = db.query(ReferenceSpectrum).filter(ReferenceSpectrum.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference spectrum not found")

    db.delete(ref)
    db.commit()

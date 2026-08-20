from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from app.database import Base


class ReferenceSpectrum(Base):
    __tablename__ = "reference_spectra"

    id = Column(Integer, primary_key=True, index=True)

    # Core identification
    drug_name = Column(String(255), nullable=False, index=True)
    generic_name = Column(String(255), nullable=True)
    brand_name = Column(String(255), nullable=True)
    strength = Column(String(100), nullable=True)        # e.g. "500 mg"
    dosage_form = Column(String(100), nullable=True)     # e.g. "Tablet", "Capsule"
    manufacturer = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)         # Country of manufacture

    # Drug information
    description = Column(Text, nullable=True)
    uses = Column(Text, nullable=True)
    storage_conditions = Column(String(500), nullable=True)
    license_number = Column(String(100), nullable=True)  # Regulatory license / NDA number

    # Spectral metadata
    batch_reference = Column(String(100), nullable=True)
    wavenumber_data = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=False)       # JSON string: "[400.0, 402.5, ...]"
    intensity_data = Column(Text().with_variant(LONGTEXT, "mysql"), nullable=False)        # JSON string
    wavenumber_range = Column(String(100), nullable=True)  # e.g. "400–1800 cm⁻¹"
    num_measurements = Column(Integer, nullable=True)    # Number of Raman measurements averaged
    similarity_threshold = Column(Float, nullable=True)  # Drug-specific threshold override
    spectrum_info = Column(Text, nullable=True)          # Free-text spectrum acquisition info

    # Multi-source dataset & provenance fields
    dataset_id = Column(String(100), nullable=True)
    dataset_name = Column(String(255), nullable=True)
    source_institution = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    doi = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    sample_type = Column(String(100), nullable=True)
    spectral_range_original = Column(String(100), nullable=True)
    spectral_resolution_original = Column(String(100), nullable=True)
    laser_wavelength = Column(String(100), nullable=True)
    spectrometer = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=True)
    original_sample_id = Column(String(100), nullable=True)
    preprocessing_method = Column(String(255), nullable=True)
    missing_range = Column(String(255), nullable=True)
    sample_status = Column(String(50), nullable=True, default="AUTHENTIC")
    reference_status = Column(String(50), nullable=True, default="ACTIVE")

    source = Column(String(255), nullable=True)
    added_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    added_by_user = relationship("User", foreign_keys=[added_by],
                                 primaryjoin="ReferenceSpectrum.added_by == User.id")



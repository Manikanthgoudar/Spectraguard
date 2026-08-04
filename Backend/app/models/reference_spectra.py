from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
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
    wavenumber_data = Column(Text, nullable=False)       # JSON string: "[400.0, 402.5, ...]"
    intensity_data = Column(Text, nullable=False)        # JSON string
    wavenumber_range = Column(String(100), nullable=True)  # e.g. "400–1800 cm⁻¹"
    num_measurements = Column(Integer, nullable=True)    # Number of Raman measurements averaged
    similarity_threshold = Column(Float, nullable=True)  # Drug-specific threshold override
    spectrum_info = Column(Text, nullable=True)          # Free-text spectrum acquisition info

    source = Column(String(255), nullable=True)
    added_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    added_by_user = relationship("User", foreign_keys=[added_by],
                                 primaryjoin="ReferenceSpectrum.added_by == User.id")

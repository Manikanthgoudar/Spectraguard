from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ReferenceSpectrum(Base):
    __tablename__ = "reference_spectra"

    id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String(255), nullable=False, index=True)
    manufacturer = Column(String(255), nullable=True)
    batch_reference = Column(String(100), nullable=True)
    # Store as JSON string: "[400.0, 402.5, ...]"
    wavenumber_data = Column(Text, nullable=False)
    intensity_data = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    added_by_user = relationship("User", foreign_keys=[added_by])

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ClassificationResult(str, enum.Enum):
    genuine = "genuine"
    potentially_counterfeit = "potentially_counterfeit"
    requires_verification = "requires_verification"
    pending = "pending"


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    drug_name = Column(String(255), nullable=False)
    batch_number = Column(String(100), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    expiry_date = Column(String(50), nullable=True)
    uploaded_csv_path = Column(String(500), nullable=True)
    classification_result = Column(
        Enum(ClassificationResult),
        default=ClassificationResult.pending,
        nullable=False,
    )
    confidence_score = Column(Float, nullable=True)
    matched_reference_id = Column(
        Integer, ForeignKey("reference_spectra.id"), nullable=True
    )
    tested_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    matched_reference = relationship("ReferenceSpectrum", foreign_keys=[matched_reference_id])
    spectra_data = relationship("SpectraData", back_populates="test", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="test", uselist=False, cascade="all, delete-orphan")

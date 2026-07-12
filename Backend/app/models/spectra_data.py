from sqlalchemy import Column, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class SpectraData(Base):
    __tablename__ = "spectra_data"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    # Store full arrays as JSON for efficient retrieval
    wavenumber_data = Column(Text, nullable=False)
    intensity_data = Column(Text, nullable=False)

    test = relationship("Test", back_populates="spectra_data")

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), unique=True, nullable=False)
    report_pdf_path = Column(String(500), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test", back_populates="report")

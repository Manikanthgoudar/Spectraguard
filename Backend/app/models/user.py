import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text
from app.database import Base


class UserRole(str, enum.Enum):
    public = "public"
    pharmacist = "pharmacist"
    investigator = "investigator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.public, nullable=False)
    organization = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

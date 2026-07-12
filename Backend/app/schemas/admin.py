from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.user import UserRole
from app.schemas.auth import UserResponse


class AdminStats(BaseModel):
    total_tests: int
    total_users: int
    counterfeit_count: int
    genuine_count: int
    requires_verification_count: int
    counterfeit_detection_rate: float
    most_tested_drugs: List[Dict[str, Any]]
    users_by_role: Dict[str, int]


class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[int] = None
    organization: Optional[str] = None
    designation: Optional[str] = None


class UserAdminResponse(UserResponse):
    is_active: int
    created_at: Any = None

    model_config = {"from_attributes": True}

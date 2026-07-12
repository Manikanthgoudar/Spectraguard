from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, UserRole
from app.models.test import Test, ClassificationResult
from app.schemas.admin import AdminStats, UserAdminUpdate, UserAdminResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Aggregate statistics for the admin dashboard."""
    total_tests = db.query(Test).count()
    total_users = db.query(User).count()

    counterfeit_count = db.query(Test).filter(
        Test.classification_result == ClassificationResult.potentially_counterfeit
    ).count()

    genuine_count = db.query(Test).filter(
        Test.classification_result == ClassificationResult.genuine
    ).count()

    requires_count = db.query(Test).filter(
        Test.classification_result == ClassificationResult.requires_verification
    ).count()

    counterfeit_rate = round((counterfeit_count / total_tests * 100), 2) if total_tests > 0 else 0.0

    # Most tested drugs (top 10)
    drug_counts = (
        db.query(Test.drug_name, func.count(Test.id).label("count"))
        .group_by(Test.drug_name)
        .order_by(func.count(Test.id).desc())
        .limit(10)
        .all()
    )
    most_tested_drugs = [{"drug_name": row.drug_name, "count": row.count} for row in drug_counts]

    # Users by role
    role_counts = (
        db.query(User.role, func.count(User.id).label("count"))
        .group_by(User.role)
        .all()
    )
    users_by_role = {row.role.value: row.count for row in role_counts}

    return AdminStats(
        total_tests=total_tests,
        total_users=total_users,
        counterfeit_count=counterfeit_count,
        genuine_count=genuine_count,
        requires_verification_count=requires_count,
        counterfeit_detection_rate=counterfeit_rate,
        most_tested_drugs=most_tested_drugs,
        users_by_role=users_by_role,
    )


@router.get("/users", response_model=List[UserAdminResponse])
def list_users(
    role: Optional[UserRole] = Query(None),
    is_active: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users with optional filters (admin only)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.patch("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's role, status, or profile (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

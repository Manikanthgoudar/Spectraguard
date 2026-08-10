from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.test import Test, ClassificationResult
from app.schemas.test import TestResponse, TestListResponse

router = APIRouter(prefix="/tests", tags=["Test History"])


@router.get("", response_model=TestListResponse)
def list_tests(
    drug_name: Optional[str] = Query(None, description="Filter by drug name (partial match)"),
    result: Optional[ClassificationResult] = Query(None, description="Filter by classification result"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    all_users: bool = Query(False, description="Admin only: set to true to list tests across all users"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tests for the current user with optional filters."""
    query = db.query(Test)

    if not (all_users and current_user.role == UserRole.admin):
        query = query.filter(Test.user_id == current_user.id)

    if drug_name:
        query = query.filter(Test.drug_name.ilike(f"%{drug_name}%"))
    if result:
        query = query.filter(Test.classification_result == result)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Test.tested_at >= dt_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format, use YYYY-MM-DD")
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(Test.tested_at <= dt_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format, use YYYY-MM-DD")

    total = query.count()
    tests = query.order_by(Test.tested_at.desc()).offset(skip).limit(limit).all()

    return TestListResponse(tests=tests, total=total)


@router.get("/{test_id}", response_model=TestResponse)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a single test."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a test record (and associated spectra/report via cascade)."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if current_user.role != UserRole.admin and test.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(test)
    db.commit()

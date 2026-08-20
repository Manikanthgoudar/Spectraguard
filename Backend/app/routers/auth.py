import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.core.logging_config import logger
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenResponse, RefreshTokenRequest,
    UserResponse, UpdateProfileRequest, ChangePasswordRequest, ChangeEmailRequest,
)

# Directory where profile photos are stored
PHOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user (role-based, with conditional field validation)."""
    email_clean = payload.email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email_clean,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        role=payload.role,
        organization=payload.organization,
        license_number=payload.license_number,
        designation=payload.designation,
        city=payload.city,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens.
    
    Valid credentials always succeed. The active_device_id is updated to the
    current device, naturally migrating the session if the user switches devices
    or their stored device_id was lost (e.g. cleared browser storage on web).
    Use /auth/force-login for the same behavior explicitly.
    """
    email_clean = payload.email.strip().lower()
    logger.info("Login attempt for email=%s device=%s", email_clean, payload.device_id)
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if not user:
        logger.warning("Login failed for email=%s — user not found", email_clean)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        logger.warning("Login failed for email=%s — inactive account", email_clean)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact support.",
        )

    if not verify_password(payload.password, user.password_hash):
        logger.warning("Login failed for email=%s — incorrect password", email_clean)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update the active device — valid credentials are sufficient
    user.active_device_id = payload.device_id
    db.commit()

    token_data = {"sub": str(user.id), "role": user.role.value, "device_id": payload.device_id}
    tokens = TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )
    logger.info("Login successful for user_id=%s email=%s", user.id, user.email)
    return tokens


@router.post("/force-login", response_model=TokenResponse)
def force_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Force login — kicks out any existing session and logs in on the new device."""
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact support.",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Override whatever device was active before
    user.active_device_id = payload.device_id
    db.commit()

    token_data = {"sub": str(user.id), "role": user.role.value, "device_id": payload.device_id}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear the active device session so the user can log in elsewhere."""
    current_user.active_device_id = None
    db.commit()
    return {"detail": "Logged out successfully"}


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    token_data = {"sub": decoded["sub"], "role": decoded["role"]}
    # Preserve device_id so the refreshed access token still passes the
    # device-session check in dependencies.py.
    if decoded.get("device_id"):
        token_data["device_id"] = decoded["device_id"]
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    logger.info("Profile fetched for user_id=%s email=%s", current_user.id, current_user.email)
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the currently authenticated user's editable profile fields."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently deactivate (soft-delete) the authenticated user's account."""
    current_user.is_active = 0
    current_user.active_device_id = None
    db.commit()


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password after verifying the existing one."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password changed successfully"}


@router.post("/me/change-email", response_model=UserResponse)
def change_email(
    payload: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's email address after verifying password."""
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        )
    existing = db.query(User).filter(
        User.email == payload.new_email,
        User.id != current_user.id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already in use by another account",
        )
    current_user.email = payload.new_email
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/photo", response_model=UserResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload or replace the user's profile photo (JPEG/PNG/WebP, max 5 MB)."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are supported",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_PHOTO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile photo must be smaller than 5 MB",
        )

    # Remove old photo if present
    if current_user.profile_photo:
        old_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            current_user.profile_photo.lstrip("/"),
        )
        if os.path.isfile(old_path):
            os.remove(old_path)

    # Save new photo with a unique filename
    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(PHOTOS_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(contents)

    # Store the URL path relative to server root
    current_user.profile_photo = f"/uploads/photos/{filename}"
    db.commit()
    db.refresh(current_user)
    logger.info("Profile photo updated for user_id=%s", current_user.id)
    return current_user


@router.delete("/me/photo", response_model=UserResponse)
def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove the user's profile photo."""
    if current_user.profile_photo:
        old_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            current_user.profile_photo.lstrip("/"),
        )
        if os.path.isfile(old_path):
            os.remove(old_path)
        current_user.profile_photo = None
        db.commit()
        db.refresh(current_user)
    return current_user

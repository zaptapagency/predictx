from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.models_saas import User, Organization
from app.database import get_db
from app.services.auth_service import AuthService
from app.database import get_db
from app.utils import setup_logger
from app.database import get_db

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_verified: bool
    is_active: bool
    organization_id: Optional[int] = None
    last_login: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_db), db: Session = Depends(get_db)):
    """Get current user profile"""
    try:
        return current_user

    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """Update user profile"""
    try:
        if request.full_name:
            current_user.full_name = request.full_name

        if request.username:
            # Check if username is taken
            existing = (
                db.query(User)
                .filter(User.username == request.username, User.id != current_user.id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Username already taken")

            current_user.username = request.username

        db.commit()
        db.refresh(current_user)

        logger.info(f"User profile updated: {current_user.email}")

        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """Change user password"""
    try:
        if not AuthService.verify_password(request.old_password, current_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")

        current_user.hashed_password = AuthService.hash_password(request.new_password)
        db.commit()

        logger.info(f"Password changed: {current_user.email}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.get("/organization", response_model=OrganizationResponse)
async def get_organization(current_user: User = Depends(get_db), db: Session = Depends(get_db)):
    """Get user's organization"""
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=404, detail="Organization not found")

        organization = db.query(Organization).filter_by(id=current_user.organization_id).first()

        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        return organization

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get organization")


@router.delete("/me")
async def delete_account(current_user: User = Depends(get_db), db: Session = Depends(get_db)):
    """Delete user account (soft delete)"""
    try:
        current_user.is_active = False
        db.commit()

        logger.info(f"Account deactivated: {current_user.email}")

        return {"message": "Account deactivated successfully"}

    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete account")

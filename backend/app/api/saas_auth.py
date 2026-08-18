from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.models_saas import User, Organization
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.config import settings
from app.utils import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    user_id: int
    token: str


@router.post("/signup")
async def signup(request: SignupRequest, db: Session = Depends()):
    """Register new user"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_username = db.query(User).filter(User.username == request.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")

        # Create user
        user = User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            hashed_password=AuthService.hash_password(request.password),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Create organization
        organization = Organization(
            name=f"{request.full_name}'s Organization",
            slug=request.username,
            owner_id=user.id,
            billing_email=request.email,
        )

        db.add(organization)
        db.commit()

        # Update user organization
        user.organization_id = organization.id
        db.commit()

        # Send welcome email
        EmailService.send_welcome_email(request.email, request.full_name)

        # Create verification token
        verification_token = AuthService.create_verification_token(db, user.id)

        # In production, send email with link
        verification_link = f"{settings.FRONTEND_URL}/verify-email?user_id={user.id}&token={verification_token}"

        EmailService.send_verification_email(request.email, verification_link)

        # Create tokens
        access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})

        logger.info(f"User signed up: {user.email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Signup failed")


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends()):
    """Login user"""
    try:
        user = db.query(User).filter(User.email == request.email).first()

        if not user or not AuthService.verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create tokens
        access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})

        logger.info(f"User logged in: {user.email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "organization_id": user.organization_id,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, db: Session = Depends()):
    """Verify email address"""
    try:
        if AuthService.verify_email_token(db, request.user_id, request.token):
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")


@router.post("/password-reset")
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends()):
    """Request password reset"""
    try:
        user = db.query(User).filter(User.email == request.email).first()

        if not user:
            # Don't reveal if email exists
            return {"message": "If email exists, password reset link will be sent"}

        # Create reset token
        reset_token = AuthService.create_password_reset_token(db, user.id)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # Send email
        EmailService.send_password_reset_email(user.email, reset_link)

        logger.info(f"Password reset requested: {user.email}")

        return {"message": "Password reset link sent to email"}

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset request failed")


@router.post("/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends()):
    """Confirm password reset"""
    try:
        if AuthService.reset_password(db, request.token, request.new_password):
            return {"message": "Password reset successful"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirm error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.models_saas import User, Organization
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.config import settings
from app.utils import setup_logger
from app.database import get_db

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
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register new user - DEBUG VERSION"""
    try:
        print(f"[DEBUG] Starting signup for {request.email}")

        # Step 1: Check DB connection
        try:
            result = db.query(User).filter(User.email == request.email).first()
            print(f"[DEBUG] DB check 1 passed, existing user: {result}")
        except Exception as e:
            print(f"[ERROR] DB check 1 failed: {e}")
            raise Exception(f"Database check failed: {e}")

        if result:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Step 2: Check username
        try:
            result = db.query(User).filter(User.username == request.username).first()
            print(f"[DEBUG] DB check 2 passed, existing username: {result}")
        except Exception as e:
            print(f"[ERROR] DB check 2 failed: {e}")
            raise Exception(f"Username check failed: {e}")

        if result:
            raise HTTPException(status_code=400, detail="Username already taken")

        # Step 3: Hash password
        try:
            hashed = AuthService.hash_password(request.password)
            print(f"[DEBUG] Password hashed successfully")
        except Exception as e:
            print(f"[ERROR] Password hash failed: {e}")
            raise Exception(f"Password hash failed: {e}")

        # Step 4: Create user object
        try:
            user = User(
                email=request.email,
                username=request.username,
                full_name=request.full_name,
                hashed_password=hashed,
                is_verified=True,
                is_active=True
            )
            print(f"[DEBUG] User object created")
        except Exception as e:
            print(f"[ERROR] User object creation failed: {e}")
            raise Exception(f"User object creation failed: {e}")

        # Step 5: Add to DB
        try:
            db.add(user)
            print(f"[DEBUG] User added to session")
        except Exception as e:
            print(f"[ERROR] Add to DB failed: {e}")
            raise Exception(f"Add to DB failed: {e}")

        # Step 6: Commit
        try:
            db.commit()
            print(f"[DEBUG] Commit successful")
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Commit failed: {e}")
            raise Exception(f"Commit failed: {e}")

        # Step 7: Refresh
        try:
            db.refresh(user)
            print(f"[DEBUG] Refresh successful, user ID: {user.id}")
        except Exception as e:
            print(f"[ERROR] Refresh failed: {e}")
            raise Exception(f"Refresh failed: {e}")

        # Step 8: Create tokens
        try:
            access_token = AuthService.create_access_token({"sub": str(user.id), "email": user.email})
            refresh_token = AuthService.create_refresh_token({"sub": str(user.id)})
            print(f"[DEBUG] Tokens created successfully")
        except Exception as e:
            print(f"[ERROR] Token creation failed: {e}")
            raise Exception(f"Token creation failed: {e}")

        print(f"[DEBUG] Signup complete for {user.email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "username": user.username, "full_name": user.full_name, "is_verified": True},
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[FATAL] Signup failed: {error_msg}")
        raise HTTPException(status_code=500, detail=f"DEBUG: {error_msg}")


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
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
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
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
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
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
async def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
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

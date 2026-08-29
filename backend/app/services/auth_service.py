from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.db.models_saas import User, PasswordResetToken
from app.utils import setup_logger
import secrets
from app.utils.time import utcnow

logger = setup_logger(__name__)

_bearer_scheme = HTTPBearer()


class AuthService:
    """Authentication service for SaaS"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt directly (avoids passlib's broken bcrypt version probe)"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = utcnow() + expires_delta
        else:
            expire = utcnow() + timedelta(
                hours=settings.JWT_EXPIRATION_HOURS
            )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create refresh token (valid for 30 days)"""
        to_encode = data.copy()
        expire = utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def create_verification_token(db: Session, user_id: int) -> str:
        """Create email verification token"""
        token = secrets.token_urlsafe(32)
        token_hash = AuthService.hash_password(token)

        # Store hash in database
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.verification_token = token_hash
            user.verification_token_expires = utcnow() + timedelta(hours=24)
            db.commit()

        return token

    @staticmethod
    def verify_email_token(db: Session, user_id: int, token: str) -> bool:
        """Verify email token"""
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.verification_token:
            return False

        if user.verification_token_expires < utcnow():
            return False

        if AuthService.verify_password(token, user.verification_token):
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            db.commit()
            return True

        return False

    @staticmethod
    def create_password_reset_token(db: Session, user_id: int) -> str:
        """Create password reset token"""
        token = secrets.token_urlsafe(32)
        token_hash = AuthService.hash_password(token)

        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=utcnow() + timedelta(hours=24),
        )

        db.add(reset_token)
        db.commit()

        return token

    @staticmethod
    def verify_password_reset_token(db: Session, token: str) -> Optional[int]:
        """Verify password reset token and return user_id"""
        try:
            reset_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > utcnow(),
            ).all()

            for rt in reset_tokens:
                if AuthService.verify_password(token, rt.token_hash):
                    return rt.user_id

            return None
        except Exception as e:
            logger.error(f"Error verifying password reset token: {str(e)}")
            return None

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset password with token"""
        user_id = AuthService.verify_password_reset_token(db, token)

        if not user_id:
            return False

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        user.hashed_password = AuthService.hash_password(new_password)

        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_used == False,
        ).first()

        if reset_token:
            reset_token.is_used = True

        db.commit()

        logger.info(f"Password reset for user: {user.email}")

        return True


# Module-level helpers, used as FastAPI dependencies / plain functions by the
# feature routers (predictions, playbooks, connectors, etc). Thin wrappers
# around AuthService so there is a single source of truth for the JWT logic.

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return AuthService.create_access_token(data, expires_delta)


def hash_password(password: str) -> str:
    return AuthService.hash_password(password)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: resolve the bearer token to a logged-in User."""
    payload = AuthService.verify_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user

import secrets
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.models_saas import APIKey, User
from app.utils import setup_logger

logger = setup_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class APIKeyService:
    """API Key management service"""

    @staticmethod
    def generate_api_key() -> tuple:
        """Generate new API key (prefix + secret)"""
        secret = secrets.token_urlsafe(32)
        prefix = secret[:8]
        return prefix, secret

    @staticmethod
    def create_api_key(
        db: Session,
        user_id: int,
        name: str,
        permissions: Optional[Dict] = None,
        expires_in_days: Optional[int] = None,
    ) -> Optional[Dict]:
        """Create new API key"""
        try:
            prefix, secret = APIKeyService.generate_api_key()
            key_hash = pwd_context.hash(secret)

            # Default permissions
            if permissions is None:
                permissions = {"read": True, "write": False}

            api_key = APIKey(
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                prefix=prefix,
                permissions=permissions,
            )

            if expires_in_days:
                from datetime import datetime, timedelta

                api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            db.add(api_key)
            db.commit()
            db.refresh(api_key)

            logger.info(f"Created API key for user: {user_id}")

            return {
                "id": api_key.id,
                "name": api_key.name,
                "prefix": api_key.prefix,
                "secret": secret,  # Only return once!
                "permissions": api_key.permissions,
                "created_at": api_key.created_at.isoformat(),
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            }

        except Exception as e:
            logger.error(f"Error creating API key: {str(e)}")
            db.rollback()
            return None

    @staticmethod
    def verify_api_key(db: Session, prefix: str, secret: str) -> Optional[User]:
        """Verify API key and return user"""
        try:
            from datetime import datetime

            api_key = (
                db.query(APIKey)
                .filter(APIKey.prefix == prefix, APIKey.is_active == True)
                .first()
            )

            if not api_key:
                return None

            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None

            # Verify secret
            if not pwd_context.verify(secret, api_key.key_hash):
                return None

            # Update last used
            api_key.last_used_at = datetime.utcnow()
            api_key.usage_count += 1
            db.commit()

            logger.info(f"API key verified: {prefix}")

            return api_key.user

        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            return None

    @staticmethod
    def list_api_keys(db: Session, user_id: int) -> List[Dict]:
        """List user's API keys"""
        try:
            keys = (
                db.query(APIKey)
                .filter(APIKey.user_id == user_id)
                .order_by(APIKey.created_at.desc())
                .all()
            )

            return [
                {
                    "id": key.id,
                    "name": key.name,
                    "prefix": key.prefix,
                    "permissions": key.permissions,
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                    "usage_count": key.usage_count,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                }
                for key in keys
            ]

        except Exception as e:
            logger.error(f"Error listing API keys: {str(e)}")
            return []

    @staticmethod
    def revoke_api_key(db: Session, key_id: int, user_id: int) -> bool:
        """Revoke API key"""
        try:
            api_key = (
                db.query(APIKey)
                .filter(APIKey.id == key_id, APIKey.user_id == user_id)
                .first()
            )

            if not api_key:
                return False

            api_key.is_active = False
            db.commit()

            logger.info(f"Revoked API key: {api_key.prefix}")

            return True

        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def update_api_key_permissions(
        db: Session, key_id: int, user_id: int, permissions: Dict
    ) -> bool:
        """Update API key permissions"""
        try:
            api_key = (
                db.query(APIKey)
                .filter(APIKey.id == key_id, APIKey.user_id == user_id)
                .first()
            )

            if not api_key:
                return False

            api_key.permissions = permissions
            db.commit()

            logger.info(f"Updated permissions for API key: {api_key.prefix}")

            return True

        except Exception as e:
            logger.error(f"Error updating API key permissions: {str(e)}")
            db.rollback()
            return False

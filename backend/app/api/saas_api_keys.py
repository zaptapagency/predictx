from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.db.models_saas import User
from app.database import get_db
from app.services.api_key_service import APIKeyService
from app.utils import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


class CreateAPIKeyRequest(BaseModel):
    name: str
    permissions: Optional[Dict] = None
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    permissions: Dict
    last_used_at: Optional[str] = None
    usage_count: int
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None


class APIKeyCreateResponse(BaseModel):
    id: int
    name: str
    prefix: str
    secret: str  # Only returned on creation
    permissions: Dict
    created_at: str
    expires_at: Optional[str] = None


class UpdatePermissionsRequest(BaseModel):
    permissions: Dict


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(current_user: User = Depends(get_db), db: Session = Depends(get_db)):
    """List all API keys for user"""
    try:
        keys = APIKeyService.list_api_keys(db, current_user.id)
        return keys

    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/", response_model=APIKeyCreateResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """Create new API key"""
    try:
        api_key = APIKeyService.create_api_key(
            db,
            current_user.id,
            request.name,
            request.permissions,
            request.expires_in_days,
        )

        if not api_key:
            raise HTTPException(status_code=400, detail="Failed to create API key")

        logger.info(f"API key created for user: {current_user.email}")

        return api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """Revoke API key"""
    try:
        if not APIKeyService.revoke_api_key(db, key_id, current_user.id):
            raise HTTPException(status_code=404, detail="API key not found")

        logger.info(f"API key revoked: {key_id}")

        return {"message": "API key revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.put("/{key_id}/permissions")
async def update_api_key_permissions(
    key_id: int,
    request: UpdatePermissionsRequest,
    current_user: User = Depends(get_db),
    db: Session = Depends(get_db),
):
    """Update API key permissions"""
    try:
        if not APIKeyService.update_api_key_permissions(
            db, key_id, current_user.id, request.permissions
        ):
            raise HTTPException(status_code=404, detail="API key not found")

        logger.info(f"API key permissions updated: {key_id}")

        return {"message": "Permissions updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update permissions")

"""
Temporary maintenance endpoints.

One-off cleanup of test accounts created before signup required a real
password. Guarded by MAINTENANCE_TOKEN and hard-restricted to @example.com
addresses (RFC 2606 reserved test domain) so real user accounts cannot be
touched. DELETE THIS MODULE once the cleanup is done.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_saas import User, Organization

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

# Only addresses on this reserved test domain are ever eligible for deletion.
TEST_DOMAIN = "@example.com"


def _authorize(x_maintenance_token: str = Header(None)):
    expected = os.getenv("MAINTENANCE_TOKEN")
    if not expected:
        raise HTTPException(status_code=404, detail="Not found")
    if x_maintenance_token != expected:
        raise HTTPException(status_code=403, detail="Invalid maintenance token")
    return True


@router.get("/test-accounts")
def list_test_accounts(
    _: bool = Depends(_authorize),
    db: Session = Depends(get_db),
):
    """List every account, flagging which are eligible for deletion."""
    users = db.query(User).order_by(User.id).all()
    return {
        "total": len(users),
        "eligible_for_deletion": sum(1 for u in users if u.email.endswith(TEST_DOMAIN)),
        "accounts": [
            {
                "id": u.id,
                "email": u.email,
                "organization_id": u.organization_id,
                "created_at": u.created_at,
                "is_test": u.email.endswith(TEST_DOMAIN),
            }
            for u in users
        ],
    }


@router.post("/test-accounts/delete")
def delete_test_accounts(
    _: bool = Depends(_authorize),
    db: Session = Depends(get_db),
):
    """Delete accounts on the reserved test domain and their organizations."""
    users = db.query(User).filter(User.email.like(f"%{TEST_DOMAIN}")).all()

    deleted, org_ids = [], set()
    for u in users:
        # Belt-and-braces: never delete anything off the test domain.
        if not u.email.endswith(TEST_DOMAIN):
            continue
        deleted.append({"id": u.id, "email": u.email})
        if u.organization_id:
            org_ids.add(u.organization_id)
        db.delete(u)
    db.flush()

    # Drop organizations that no longer have any members.
    orgs_deleted = []
    for oid in org_ids:
        remaining = db.query(User).filter(User.organization_id == oid).count()
        if remaining == 0:
            org = db.query(Organization).filter(Organization.id == oid).first()
            if org:
                orgs_deleted.append(oid)
                db.delete(org)

    db.commit()
    return {
        "deleted_users": len(deleted),
        "deleted_organizations": len(orgs_deleted),
        "accounts": deleted,
    }

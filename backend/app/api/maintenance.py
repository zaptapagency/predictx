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
    # Belt-and-braces: never touch anything off the reserved test domain.
    users = [u for u in users if u.email.endswith(TEST_DOMAIN)]
    if not users:
        return {"deleted_users": 0, "deleted_organizations": 0, "accounts": []}

    user_ids = [u.id for u in users]
    deleted = [{"id": u.id, "email": u.email} for u in users]

    # Only drop organizations whose every member is being deleted.
    candidate_orgs = {u.organization_id for u in users if u.organization_id}
    org_ids = [
        oid for oid in candidate_orgs
        if db.query(User).filter(
            User.organization_id == oid, ~User.id.in_(user_ids)
        ).count() == 0
    ]

    from sqlalchemy import text
    from app.db.database import Base

    # Delete child rows first: sorted_tables is parents-first, so walk it
    # in reverse and clear anything pointing at these users or orgs.
    for table in reversed(Base.metadata.sorted_tables):
        if table.name in ("users", "organizations"):
            continue
        for col in table.columns:
            for fk in col.foreign_keys:
                target = fk.column.table.name
                ids = user_ids if target == "users" else org_ids if target == "organizations" else None
                if not ids:
                    continue
                db.execute(
                    text(f'DELETE FROM "{table.name}" WHERE "{col.name}" = ANY(:ids)'),
                    {"ids": ids},
                )

    # Break the users <-> organizations cycle before deleting either side.
    if org_ids:
        db.execute(
            text('UPDATE organizations SET owner_id = NULL WHERE owner_id = ANY(:ids)'),
            {"ids": user_ids},
        )
    db.execute(text('DELETE FROM users WHERE id = ANY(:ids)'), {"ids": user_ids})
    if org_ids:
        db.execute(text('DELETE FROM organizations WHERE id = ANY(:ids)'), {"ids": org_ids})

    db.commit()
    return {
        "deleted_users": len(deleted),
        "deleted_organizations": len(org_ids),
        "accounts": deleted,
    }

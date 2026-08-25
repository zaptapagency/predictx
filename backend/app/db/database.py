"""Database session/base for the product feature models (predictions, playbooks,
connectors, marketplace, etc). Shares the same engine AND the same declarative
Base as the SaaS auth models, so cross-model foreign keys and string-based
relationship("User")/relationship("Organization") references resolve correctly
within a single SQLAlchemy registry."""

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.db.models_saas import Base


def get_db() -> Session:
    """Get database session dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

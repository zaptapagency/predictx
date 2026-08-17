"""Initialize database and create tables"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from app.config import settings
from app.db.models import Base

def setup_database():
    """Create database tables"""

    print(f"Connecting to: {settings.DATABASE_URL}")

    engine = create_engine(settings.DATABASE_URL)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    setup_database()

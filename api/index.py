import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import FastAPI app
from app.main import app

# Vercel expects the app to be called 'app' for ASGI
# No additional handler needed - Vercel will use the ASGI protocol

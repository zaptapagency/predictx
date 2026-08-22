import sys
import os

# FastAPI app is in the parent directory structure
from app.main import app

# Vercel ASGI handler
# app is exported directly for Vercel's Python runtime

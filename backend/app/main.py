from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import subprocess
import os
from sqlalchemy.orm import Session

from app.config import settings
from app.utils import setup_logger
from app.api import saas_auth, saas_subscriptions, saas_api_keys, saas_user, saas_admin, webhooks
from app.database import get_db, engine
from app.db.models_saas import User

logger = setup_logger(__name__)


def run_migrations():
    """Run Alembic migrations on startup"""
    try:
        if os.path.exists('/app/alembic.ini'):
            logger.info("Running database migrations...")
            result = subprocess.run(
                ['python', '-m', 'alembic', 'upgrade', 'head'],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("✅ Migrations completed successfully")
            else:
                logger.warning(f"Migration output: {result.stdout}\n{result.stderr}")
    except Exception as e:
        logger.warning(f"Could not run migrations: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
    )

    # CORS Middleware - Allow all origins with full configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )

    # Include routers
    app.include_router(saas_auth.router)
    app.include_router(saas_subscriptions.router)
    app.include_router(saas_api_keys.router)
    app.include_router(saas_user.router)
    app.include_router(saas_admin.router)
    app.include_router(webhooks.router)

    # Startup event - Run migrations
    @app.on_event("startup")
    async def startup_event():
        run_migrations()

    # Health check
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "version": "3.0.0-LIVE",
            "environment": settings.ENVIRONMENT,
            "message": "New code is running!",
        }

    # Simple debug endpoint
    @app.get("/api/debug/version")
    async def debug_version():
        return {"version": "3.0.0", "timestamp": "2026-08-22"}

    @app.post("/api/debug/test-db")
    async def debug_test_db(db: Session = Depends(get_db)):
        try:
            result = db.query(User).first()
            return {"status": "DB connected", "users_exist": result is not None}
        except Exception as e:
            return {"status": "DB error", "error": str(e)}

    # Migration trigger endpoint
    @app.post("/admin/migrate")
    async def trigger_migrations():
        """Trigger database migrations (admin only)"""
        try:
            run_migrations()
            return {"status": "success", "message": "Migrations completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "PredictX SaaS API",
            "version": settings.API_VERSION,
            "docs": "/docs",
        }


    # Schema fix endpoint
    @app.post("/admin/fix-schema")
    async def fix_schema():
        """Fix missing database columns"""
        try:
            from app.database import engine
            with engine.connect() as conn:
                # Add missing columns if they don't exist
                commands = [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR UNIQUE;",
                ]
                for cmd in commands:
                    try:
                        conn.execute(cmd)
                        conn.commit()
                    except:
                        pass
            return {"status": "schema fixed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    logger.info(f"FastAPI app created: {settings.API_TITLE} v{settings.API_VERSION}")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

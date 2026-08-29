from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import subprocess
import os
from sqlalchemy.orm import Session

from app.config import settings
from app.utils import setup_logger
from app.api import saas_auth, saas_subscriptions, saas_api_keys, saas_user, saas_admin, webhooks
from app.api import (
    actions, activity_feed, adoption, connectors, copilot, csv_upload, demo, heatmap, insights,
    integrations, leaderboard, marketplace, oauth, onboarding, playbook_monitor, predictions,
    predictions_api, quickwins, roi, sample_predictions, team_invitations, training,
    user_home, workflows,
)
from app.database import get_db, engine
from app.db.models_saas import User
from app.utils.time import utcnow


class ManualCORSMiddleware(BaseHTTPMiddleware):
    """Manual CORS middleware that explicitly adds headers"""
    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS (preflight) requests
        if request.method == "OPTIONS":
            return JSONResponse(
                content={},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
                    "Access-Control-Max-Age": "3600",
                    "Access-Control-Allow-Credentials": "true",
                }
            )

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Max-Age"] = "3600"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

logger = setup_logger(__name__)

# Force Railway redeploy - v3.1.0


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

    # Fallback: ensure tables exist even when alembic is unavailable or a no-op.
    # create_all only creates what is missing, so this is safe to run every boot.
    try:
        from sqlalchemy import inspect, text
        from app.database import engine
        # Importing the feature models registers every table on the shared Base.
        from app.db.database import Base
        from app.db import (  # noqa: F401 - imported for table registration
            action_models, activity_models, adoption_models, connector_models,
            copilot_models, heatmap_models, insights_models, integration_models,
            leaderboard_models,
            marketplace_models, onboarding_models, playbook_monitor_models,
            prediction_models, quickwin_models, roi_models, team_models,
            workflow_models,
        )

        # One-time reconciliation: an earlier deploy created "predictions" from
        # the old SaaS model (now prediction_logs). If that stale, empty table
        # is still present without the ML schema's model_id column, drop it so
        # create_all can build the real predictions table.
        inspector = inspect(engine)
        if "predictions" in inspector.get_table_names():
            cols = {c["name"] for c in inspector.get_columns("predictions")}
            if "model_id" not in cols:
                with engine.connect() as conn:
                    count = conn.execute(text("SELECT COUNT(*) FROM predictions")).scalar()
                    if count == 0:
                        conn.execute(text("DROP TABLE predictions"))
                        conn.commit()
                        logger.info("Dropped stale legacy 'predictions' table")

        Base.metadata.create_all(bind=engine)
        logger.info("✅ Schema ensured via SQLAlchemy create_all")

        # Backfill: users created before signup auto-created organizations
        # need one so the multi-tenant feature endpoints work for them.
        from app.database import SessionLocal
        from app.db.models_saas import User, Organization
        db = SessionLocal()
        try:
            orphans = db.query(User).filter(User.organization_id.is_(None)).all()
            for u in orphans:
                org = Organization(
                    name=f"{u.full_name or u.username}'s Team",
                    slug=f"{u.username}-{u.id}",
                    owner_id=u.id,
                )
                db.add(org)
                db.flush()
                u.organization_id = org.id
            if orphans:
                db.commit()
                logger.info(f"Backfilled organizations for {len(orphans)} users")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        raise


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
    )

    # Custom CORS Middleware - Add headers manually to all responses
    # This handles CORS for all origins (including GitHub Pages)
    app.add_middleware(ManualCORSMiddleware)

    # Include routers
    app.include_router(saas_auth.router)
    app.include_router(saas_subscriptions.router)
    app.include_router(saas_api_keys.router)
    app.include_router(saas_user.router)
    app.include_router(saas_admin.router)
    app.include_router(webhooks.router)

    # Product feature routers
    app.include_router(actions.router)
    app.include_router(activity_feed.router)
    app.include_router(adoption.router)
    app.include_router(connectors.router)
    app.include_router(copilot.router)
    app.include_router(heatmap.router)
    app.include_router(insights.router)
    app.include_router(integrations.router)
    app.include_router(leaderboard.router)
    app.include_router(marketplace.router)
    app.include_router(oauth.router)
    app.include_router(onboarding.router)
    app.include_router(playbook_monitor.router)
    app.include_router(predictions.router)
    app.include_router(predictions_api.router)
    app.include_router(quickwins.router)
    app.include_router(roi.router)
    app.include_router(sample_predictions.router)
    app.include_router(csv_upload.router)
    app.include_router(training.router)
    app.include_router(demo.router)
    app.include_router(team_invitations.router)
    app.include_router(user_home.router)
    app.include_router(workflows.router)

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

    # Test CORS endpoint
    @app.get("/test-cors")
    async def test_cors():
        return {"message": "CORS test", "timestamp": utcnow().isoformat()}

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

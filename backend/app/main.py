from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.utils import setup_logger
from app.api import saas_auth, saas_subscriptions, saas_api_keys, saas_user, saas_admin, webhooks

logger = setup_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(saas_auth.router)
    app.include_router(saas_subscriptions.router)
    app.include_router(saas_api_keys.router)
    app.include_router(saas_user.router)
    app.include_router(saas_admin.router)
    app.include_router(webhooks.router)

    # Health check
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "PredictX SaaS API",
            "version": settings.API_VERSION,
            "docs": "/docs",
        }

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

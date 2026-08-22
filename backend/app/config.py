import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # API
    API_TITLE: str = "UniversalPredict API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://universalpredict:password@postgres:5432/universalpredict"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # LightGBM Models
    LIGHTGBM_REPO_PATH: str = "/app/lightgbm-repo"
    LIGHTGBM_REPO_URL: str = "https://github.com/yourusername/your-lightgbm-repo.git"
    LIGHTGBM_REPO_BRANCH: str = "main"

    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "universalpredict-models"
    AWS_REGION: str = "us-east-1"

    # Stripe (Optional)
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Google OAuth (Optional)
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""

    # Email (Optional)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Sentry (Optional)
    SENTRY_DSN: str = ""

    # File Upload
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "xls"]

    # Batch Processing
    BATCH_SIZE: int = 1000
    MAX_BATCH_RECORDS: int = 100000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

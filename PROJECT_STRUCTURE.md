# Project Structure Overview

Complete breakdown of all files and directories created for UniversalPredict Platform.

---

## Directory Tree

```
forecastx/
│
├── .github/
│   └── workflows/
│       ├── test.yml                    # Run tests on every push
│       ├── deploy-railway.yml          # Deploy to Railway (main branch)
│       └── deploy-digitalocean.yml     # Deploy to DigitalOcean (main branch)
│
├── backend/                            # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py                # Package init
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Settings from environment variables
│   │   │
│   │   ├── api/                       # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── predictions.py         # Prediction endpoints
│   │   │   ├── models.py              # Model management endpoints
│   │   │   ├── uploads.py             # File upload endpoints
│   │   │   ├── health.py              # Health check endpoints
│   │   │   └── auth.py                # Authentication endpoints
│   │   │
│   │   ├── ml/                        # Machine Learning Modules
│   │   │   ├── __init__.py
│   │   │   ├── model_loader.py        # Load LightGBM models from external repo
│   │   │   ├── feature_processor.py   # Feature engineering & preprocessing
│   │   │   ├── predictor.py           # Prediction engine
│   │   │   └── shap_explainer.py      # SHAP explanations
│   │   │
│   │   ├── db/                        # Database Layer
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   ├── session.py             # Database session
│   │   │   └── migrations/            # Alembic migrations
│   │   │
│   │   ├── schemas/                   # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── prediction.py          # Prediction request/response schemas
│   │   │   ├── user.py                # User schemas
│   │   │   ├── upload.py              # Upload schemas
│   │   │   └── batch.py               # Batch job schemas
│   │   │
│   │   ├── services/                  # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── prediction_service.py  # Prediction logic
│   │   │   ├── file_upload.py         # File upload handling
│   │   │   ├── batch_processor.py     # Batch processing
│   │   │   └── connector_service.py   # Data connector integration
│   │   │
│   │   └── utils/                     # Utilities
│   │       ├── __init__.py
│   │       ├── logger.py              # JSON logging setup
│   │       ├── validators.py          # Input validators
│   │       ├── helpers.py             # Helper functions
│   │       └── exceptions.py          # Custom exceptions
│   │
│   ├── tests/                         # Backend Tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest configuration
│   │   ├── test_api.py               # API endpoint tests
│   │   ├── test_predictions.py       # Prediction logic tests
│   │   ├── test_model_loader.py      # Model loader tests
│   │   └── test_feature_processor.py # Feature processor tests
│   │
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Docker image definition
│   ├── .env.example                   # Environment template
│   └── pytest.ini                     # Pytest configuration
│
├── frontend/                          # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx         # Main dashboard component
│   │   │   ├── PredictionForm.tsx    # Prediction input form
│   │   │   ├── FileUpload.tsx        # File upload component
│   │   │   ├── Results.tsx           # Results display
│   │   │   ├── ModelInfo.tsx         # Model information display
│   │   │   └── Header.tsx            # Header/navigation
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx              # Home page
│   │   │   ├── Predictions.tsx       # Predictions page
│   │   │   └── History.tsx           # Prediction history page
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts                # API client
│   │   │   ├── auth.ts               # Authentication service
│   │   │   └── storage.ts            # Local storage service
│   │   │
│   │   ├── types/
│   │   │   ├── prediction.ts         # TypeScript types
│   │   │   └── models.ts             # Model types
│   │   │
│   │   ├── App.tsx                   # Main App component
│   │   ├── App.css                   # Styles
│   │   ├── index.tsx                 # React entry point
│   │   └── index.css                 # Global styles
│   │
│   ├── public/
│   │   ├── index.html               # HTML template
│   │   └── favicon.ico              # Favicon
│   │
│   ├── package.json                  # NPM dependencies
│   ├── package-lock.json            # Dependency lock file
│   ├── tsconfig.json                # TypeScript configuration
│   ├── Dockerfile                   # Docker image definition
│   └── .env.example                 # Environment template
│
├── scripts/                          # Utility Scripts
│   ├── setup_db.py                  # Initialize database
│   ├── load_sample_data.py          # Load sample data
│   ├── download_models.py           # Download models from S3
│   ├── upload_models_to_s3.sh       # Upload models to S3
│   └── backup_db.sh                 # Database backup
│
├── tests/                           # Integration Tests
│   ├── __init__.py
│   ├── integration_tests.py         # End-to-end tests
│   ├── load_tests.py                # Load testing
│   └── fixtures.py                  # Test fixtures
│
├── docker/                          # Docker Configuration
│   ├── docker-compose.yml           # (moved to root)
│   └── .dockerignore               # Docker build ignore
│
├── .github/                         # GitHub Configuration
│   └── workflows/                   # CI/CD Workflows
│
├── .env.example                     # Environment variables template
├── .env                            # Local environment (git ignored)
├── .gitignore                      # Git ignore rules
├── .dockerignore                   # Docker ignore rules
│
├── docker-compose.yml              # Local development setup
├── app.yaml                        # DigitalOcean app spec
├── railway.json                    # Railway configuration
│
├── README.md                       # Project documentation
├── SETUP.md                        # Detailed setup guide
├── QUICKSTART.md                   # Quick start guide
├── PROJECT_STRUCTURE.md            # This file
│
└── models/                         # (Optional) Local models directory
    ├── v1.0/                       # Model version
    │   ├── universal_model.pkl
    │   ├── universal_model_metadata.json
    │   └── feature_names.txt
    └── adapters/                   # Vertical adapters
        ├── saas_adapter.pkl
        ├── retail_adapter.pkl
        └── healthcare_adapter.pkl
```

---

## Key Files Explained

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `config.py` | Settings management using Pydantic |
| `docker-compose.yml` | Local development with Docker |
| `app.yaml` | DigitalOcean app specification |
| `railway.json` | Railway platform configuration |

### Backend Core

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/config.py` | Settings and configuration |
| `app/ml/model_loader.py` | Load pre-trained LightGBM models |
| `app/ml/feature_processor.py` | Feature engineering and preprocessing |
| `app/api/predictions.py` | Prediction endpoints |
| `app/db/models.py` | Database models (SQLAlchemy) |

### Frontend Core

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main React component |
| `src/services/api.ts` | API client and requests |
| `src/components/Dashboard.tsx` | Main dashboard UI |
| `src/components/PredictionForm.tsx` | Prediction form component |

### Docker

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Backend container definition |
| `frontend/Dockerfile` | Frontend container definition |
| `docker-compose.yml` | Multi-container local setup |

### CI/CD

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | Run tests on every push |
| `.github/workflows/deploy-railway.yml` | Deploy to Railway |
| `.github/workflows/deploy-digitalocean.yml` | Deploy to DigitalOcean |

---

## Dependencies

### Backend (Python 3.11+)

**Core Framework**
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

**Database**
- `sqlalchemy` - ORM
- `alembic` - Database migrations
- `psycopg2-binary` - PostgreSQL adapter

**ML/Data**
- `lightgbm` - Gradient boosting
- `pandas` - Data processing
- `numpy` - Numerical computing
- `shap` - Model explanations

**Security**
- `python-jose` - JWT tokens
- `passlib` - Password hashing
- `python-dotenv` - Environment variables

**Testing**
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

### Frontend (Node.js 18+)

**Core**
- `react` - UI library
- `react-dom` - React DOM
- `react-router-dom` - Routing

**HTTP**
- `axios` - HTTP client

**Dev Tools**
- `typescript` - Type safety
- `react-scripts` - Create React App

---

## Database Schema

### Tables

**predictions**
- Stores individual predictions
- Columns: id, vertical, prediction_type, features, prediction, confidence, model_version, created_at

**batch_jobs**
- Stores batch prediction jobs
- Columns: id, name, vertical, total_records, successful, failed, status, results_url

**uploads**
- Stores uploaded files
- Columns: id, filename, file_type, file_size, status, rows_count, created_at

**models**
- Stores model metadata
- Columns: id, name, version, model_type, is_active, accuracy, created_at

**users**
- Stores user accounts
- Columns: id, email, full_name, hashed_password, is_active, created_at

---

## Environment Variables

All configured in `.env`:

```env
# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# LightGBM Models
LIGHTGBM_REPO_PATH=/app/lightgbm-repo
LIGHTGBM_REPO_URL=https://github.com/...
LIGHTGBM_REPO_BRANCH=main

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=...
S3_BUCKET_NAME=...

# Application
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## API Endpoints

### Predictions
- `POST /api/predictions` - Single prediction
- `POST /api/predictions/batch` - Batch predictions
- `GET /api/predictions/{id}` - Get prediction details
- `GET /api/predictions/history` - Get history

### Models
- `GET /api/models/info` - Model information
- `GET /api/models/versions` - Available versions

### Uploads
- `POST /api/upload` - Upload file
- `GET /api/uploads` - List uploads

### Health
- `GET /health` - Health check
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

---

## Deployment Targets

### Railway
- **File**: `railway.json`
- **Features**: Auto-deploy from GitHub, PostgreSQL, Redis
- **URL**: `https://yourapp.up.railway.app`

### DigitalOcean App Platform
- **File**: `app.yaml`
- **Features**: App spec, database, auto-deploy
- **URL**: `https://yourapp.ondigitalocean.app`

### Docker Compose (Local)
- **File**: `docker-compose.yml`
- **Services**: Backend, Frontend, PostgreSQL, Redis

---

## Testing Structure

### Unit Tests
- `backend/tests/test_api.py` - API endpoint tests
- `backend/tests/test_model_loader.py` - Model loading tests

### Integration Tests
- `tests/integration_tests.py` - End-to-end tests

### Test Configuration
- `backend/pytest.ini` - Pytest settings
- `backend/tests/conftest.py` - Test fixtures

---

## Development Workflow

```
1. Make changes to code
   ├── backend/app/* (Python)
   └── frontend/src/* (React/TypeScript)

2. Test locally
   ├── docker-compose up -d
   └── Run tests: pytest, npm test

3. Commit and push
   ├── git add .
   ├── git commit -m "message"
   └── git push origin main

4. GitHub Actions runs automatically
   ├── Tests run
   ├── Build Docker images
   └── Deploy to Railway/DigitalOcean

5. Access deployed app
   └── Visit deployment URL
```

---

## Important Notes

⚠️ **Security**
- Never commit `.env` files
- Use strong JWT_SECRET_KEY
- Rotate secrets regularly
- Use HTTPS in production

📦 **Dependencies**
- Update requirements.txt when adding packages
- Use Python 3.11+
- Use Node.js 18+

🐳 **Docker**
- Build images locally before deploying
- Use `.dockerignore` to exclude files
- Tag images with version numbers

📊 **Models**
- Keep models in external repository
- Version models properly
- Store metadata with models

---

## Getting Started

1. **Read**: [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
2. **Setup**: [SETUP.md](SETUP.md) - Detailed instructions
3. **Deploy**: Follow deployment section above
4. **Manage**: Use GitHub Actions for CI/CD

---

**You now have a complete, production-ready LightGBM deployment platform!** 🚀

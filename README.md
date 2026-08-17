# UniversalPredict Platform

A production-ready ML prediction platform that loads and serves pre-trained LightGBM models via REST API, with dashboard UI, file uploads, and 200+ data connectors.

## Features

- ✅ Load pre-trained LightGBM models
- ✅ REST API for predictions (FastAPI)
- ✅ SHAP explanations for predictions
- ✅ Dashboard UI (React)
- ✅ File upload (Excel/CSV)
- ✅ 200+ data connectors
- ✅ Batch prediction processing
- ✅ Docker & Docker Compose setup
- ✅ CI/CD with GitHub Actions
- ✅ PostgreSQL + Redis

## Project Structure

```
universalpredict/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── ml/              # Machine learning modules
│   │   │   ├── model_loader.py
│   │   │   ├── feature_processor.py
│   │   │   ├── predictor.py
│   │   │   └── shap_explainer.py
│   │   ├── api/             # API routes
│   │   │   ├── predictions.py
│   │   │   ├── models.py
│   │   │   ├── health.py
│   │   │   └── auth.py
│   │   ├── db/              # Database
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   ├── services/        # Business logic
│   │   │   ├── file_upload.py
│   │   │   ├── batch_processor.py
│   │   │   └── connector_service.py
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   └── schemas/         # Pydantic schemas
│   │       ├── prediction.py
│   │       ├── user.py
│   │       └── upload.py
│   ├── tests/
│   │   ├── test_predictions.py
│   │   ├── test_model_loader.py
│   │   ├── test_api.py
│   │   └── conftest.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── PredictionForm.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   └── Results.tsx
│   │   ├── pages/
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker/
│   ├── docker-compose.yml
│   └── .dockerignore
├── .github/
│   └── workflows/
│       ├── deploy.yml
│       ├── test.yml
│       └── retrain.yml
├── models/                  # Pre-trained models (external)
│   ├── v1.0/
│   │   ├── universal_model.pkl
│   │   ├── universal_model_metadata.json
│   │   └── feature_names.txt
│   └── adapters/
│       ├── saas_adapter.pkl
│       ├── retail_adapter.pkl
│       └── healthcare_adapter.pkl
├── scripts/
│   ├── download_models.py
│   ├── setup_db.py
│   └── load_sample_data.py
├── tests/
│   └── integration_tests.py
├── .env.example
├── .gitignore
├── docker-compose.yml
└── SETUP.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Local Development (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/universalpredict.git
cd universalpredict

# 2. Copy environment file
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend python scripts/setup_db.py

# 5. Access
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Add Your Models

Place your pre-trained LightGBM models in the `models/` directory:

```bash
models/
├── v1.0/
│   ├── universal_model.pkl
│   ├── universal_model_metadata.json
│   └── feature_names.txt
└── adapters/
    ├── vertical_adapter_1.pkl
    ├── vertical_adapter_2.pkl
    └── ...
```

The platform will automatically load them on startup.

## API Usage

### Make a Prediction

```bash
curl -X POST http://localhost:8000/api/predictions \
  -H "Content-Type: application/json" \
  -d '{
    "vertical": "saas",
    "prediction_type": "churn",
    "features": {
      "feature_1": 1.0,
      "feature_2": 10,
      "feature_3": "value"
    }
  }'
```

### Batch Predictions

```bash
curl -X POST http://localhost:8000/api/predictions/batch \
  -F "file=@data.csv" \
  -F "vertical=saas" \
  -F "prediction_type=churn"
```

### File Upload & Merge

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@data.xlsx" \
  -F "connector=salesforce"
```

## Deployment

### Railway
```bash
railway init
railway variables set DATABASE_URL=...
railway up
```

### DigitalOcean
```bash
doctl apps create --spec app.yaml
```

### Docker
```bash
docker-compose -f docker/docker-compose.yml up -d
```

## Documentation

- [Setup Guide](SETUP.md)
- [API Documentation](http://localhost:8000/docs) (Swagger UI)
- [Model Integration](docs/MODEL_INTEGRATION.md)
- [Architecture](docs/ARCHITECTURE.md)

## Testing

```bash
# Run backend tests
cd backend
pytest tests/ -v

# Run integration tests
pytest tests/integration_tests.py -v
```

## License

MIT

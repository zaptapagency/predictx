FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Clone your LightGBM repo as a submodule or separate step
ARG LIGHTGBM_REPO_URL=https://github.com/yourusername/your-lightgbm-repo.git
ARG LIGHTGBM_REPO_BRANCH=main

RUN git clone \
    --depth 1 \
    --branch ${LIGHTGBM_REPO_BRANCH} \
    ${LIGHTGBM_REPO_URL} \
    lightgbm-repo

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install your lightgbm repo dependencies if needed
RUN if [ -f lightgbm-repo/requirements.txt ]; then \
    pip install --no-cache-dir -r lightgbm-repo/requirements.txt; fi

# Copy backend code
COPY backend/ /app/backend

WORKDIR /app/backend

# Set environment variable for your repo
ENV LIGHTGBM_REPO_PATH=/app/lightgbm-repo
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

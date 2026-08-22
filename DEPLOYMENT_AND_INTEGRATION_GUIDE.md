# ForecastX: Deployment and Integration Guide

## Overview

This guide covers deploying ForecastX from development to production. ForecastX is a full-stack SaaS platform consisting of:

- **Backend**: Python FastAPI + PostgreSQL
- **Frontend**: React + TypeScript
- **Services**: ML model training, workflow execution, data sync
- **Integrations**: Salesforce, CSV, Snowflake, Slack, Webhooks

---

## Pre-Deployment Checklist

### Infrastructure
- [ ] Database server (PostgreSQL 12+)
- [ ] Application server (minimum 2GB RAM, 2 CPU)
- [ ] Redis server (for caching and background jobs)
- [ ] S3 or equivalent object storage (for models, files)
- [ ] SSL certificate for HTTPS
- [ ] Domain name registered

### Code Quality
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code review completed
- [ ] Security audit passed
- [ ] No hardcoded credentials in code
- [ ] Environment variables documented

### Documentation
- [ ] API documentation complete
- [ ] Deployment guide reviewed
- [ ] Runbooks created for common issues
- [ ] Architecture diagram updated
- [ ] Change log updated

### Third-Party Services
- [ ] Salesforce OAuth app created
- [ ] Slack bot token generated
- [ ] Email service credentials (SendGrid/AWS SES)
- [ ] Stripe account set up (if billing enabled)
- [ ] Monitoring service configured (DataDog/New Relic)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Users                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼─────┐              ┌────────▼───────┐
   │ Frontend  │              │  Mobile App    │
   │ (React)   │              │  (Native)      │
   └────┬─────┘              └────────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       │
            ┌──────────▼────────────┐
            │  API Gateway / LB     │
            │  (Nginx/CloudFlare)   │
            └──────────┬────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │ Backend  │  │ Backend  │  │ Backend  │
    │ (FastAPI)│  │ (FastAPI)│  │ (FastAPI)│
    │ Instance │  │ Instance │  │ Instance │
    │    1     │  │    2     │  │    3     │
    └────┬────┘  └────┬────┘  └────┬────┘
         │            │            │
         └────────────┼────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
  ┌───▼──┐       ┌────▼───┐      ┌───▼───┐
  │ PgSQL│       │ Redis  │      │  S3   │
  │ DB   │       │ Cache  │      │ Store │
  └──────┘       └────────┘      └───────┘
```

---

## Step 1: Database Setup

### Create PostgreSQL Database

```bash
# Connect to PostgreSQL server
psql -U postgres

# Create database
CREATE DATABASE forecastx_prod ENCODING 'UTF8';
CREATE USER forecastx_user WITH PASSWORD 'secure_password_here';
ALTER ROLE forecastx_user SET client_encoding TO 'utf8';
ALTER ROLE forecastx_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE forecastx_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE forecastx_prod TO forecastx_user;
GRANT USAGE, CREATE ON SCHEMA public TO forecastx_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO forecastx_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO forecastx_user;

# Exit
\q
```

### Run Migrations

```bash
# Navigate to backend directory
cd backend

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://forecastx_user:secure_password_here@localhost:5432/forecastx_prod
SECRET_KEY=generate_a_random_key_here
ENVIRONMENT=production
EOF

# Install Python dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Verify tables created
psql -U forecastx_user -d forecastx_prod -c "\dt"
```

### Create Initial Admin User

```bash
# Create superuser via CLI
python -m app.cli create-superuser \
  --email admin@company.com \
  --password secure_password \
  --name "Admin User"

# Or via Python script
python
>>> from app.db.models_saas import User, Organization
>>> from app.db.database import SessionLocal
>>> db = SessionLocal()
>>> org = Organization(name="Company Name")
>>> db.add(org)
>>> db.commit()
>>> user = User(
...     email="admin@company.com",
...     full_name="Admin User",
...     hashed_password="hash_password_here",
...     organization_id=org.id,
...     is_admin=True
... )
>>> db.add(user)
>>> db.commit()
```

---

## Step 2: Backend Configuration

### Environment Variables

Create `backend/.env.production`:

```bash
# Database
DATABASE_URL=postgresql://forecastx_user:password@db.company.com:5432/forecastx_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Security
SECRET_KEY=your_secret_key_here_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=api.forecastx.com,*.forecastx.com

# CORS
CORS_ORIGINS=https://forecastx.com,https://app.forecastx.com

# Redis
REDIS_URL=redis://redis.company.com:6379/0

# Email Service
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_key
SMTP_FROM=noreply@forecastx.com

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your_signing_secret

# Salesforce
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REDIRECT_URI=https://api.forecastx.com/auth/salesforce/callback

# AWS S3 (for model storage)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=forecastx-models-prod
AWS_S3_REGION=us-east-1

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/forecastx/app.log

# ML Model Settings
MODEL_MAX_TRAINING_TIME=600  # seconds
MODEL_MIN_SAMPLES=50
BATCH_PREDICTION_LIMIT=10000

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_PERIOD=3600  # per hour

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key
```

### Install Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
pip install gunicorn  # WSGI server
pip install python-dotenv
```

### Start Backend Service

**Using Gunicorn** (recommended for production):

```bash
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  app.main:app
```

**Using Systemd** (for automatic restart):

Create `/etc/systemd/system/forecastx-api.service`:

```ini
[Unit]
Description=ForecastX API Service
After=network.target

[Service]
Type=notify
User=forecastx
WorkingDirectory=/opt/forecastx/backend
Environment="PATH=/opt/forecastx/backend/venv/bin"
EnvironmentFile=/opt/forecastx/backend/.env.production
ExecStart=/opt/forecastx/backend/venv/bin/gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  app.main:app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable forecastx-api
sudo systemctl start forecastx-api
sudo systemctl status forecastx-api
```

---

## Step 3: Frontend Build & Deployment

### Build React App

```bash
cd frontend

# Create .env.production
cat > .env.production << 'EOF'
REACT_APP_API_URL=https://api.forecastx.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0
EOF

# Install dependencies
npm install

# Build for production
npm run build

# Output in build/ directory
ls -lh build/
```

### Deploy to S3 + CloudFront

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Sync build to S3
aws s3 sync build/ s3://forecastx-frontend-prod \
  --delete \
  --cache-control "max-age=31536000" \
  --exclude "index.html"

# Set index.html with no cache
aws s3 cp build/index.html s3://forecastx-frontend-prod/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E123EXAMPLE456 \
  --paths "/*"
```

### Alternative: Docker Deployment

```dockerfile
# frontend/Dockerfile.prod
FROM node:16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and push:

```bash
docker build -f frontend/Dockerfile.prod -t forecastx-frontend:1.0.0 .
docker tag forecastx-frontend:1.0.0 your-registry/forecastx-frontend:1.0.0
docker push your-registry/forecastx-frontend:1.0.0
```

---

## Step 4: Background Workers Setup

### Configure Celery for Task Queue

Backend tasks include:
- Model training
- Data sync
- Workflow execution
- Batch predictions
- Email sending

**Start Worker**:

```bash
cd backend

# Single worker
celery -A app.tasks worker -l info

# Multiple workers with concurrency
celery -A app.tasks worker \
  --concurrency=4 \
  --loglevel=info \
  --logfile=/var/log/forecastx/celery.log

# With Supervisor (auto-restart)
# Create /etc/supervisor/conf.d/forecastx-worker.conf
[program:forecastx-worker]
command=/opt/forecastx/backend/venv/bin/celery -A app.tasks worker
directory=/opt/forecastx/backend
user=forecastx
numprocs=1
stdout_logfile=/var/log/forecastx/celery-worker.log
stderr_logfile=/var/log/forecastx/celery-worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600

# Start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start forecastx-worker
```

**Flower - Celery Monitoring**:

```bash
# Install
pip install flower

# Run
flower -A app.tasks --port=5555
# Access at http://localhost:5555
```

### Configure Scheduled Jobs

Model retraining, sync jobs, and maintenance tasks run on schedule.

**Using APScheduler**:

```python
# backend/app/services/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Model retraining - daily at 2 AM
scheduler.add_job(
    retrain_active_models,
    'cron',
    hour=2,
    minute=0,
    id='retrain_models'
)

# Data sync - every 6 hours
scheduler.add_job(
    sync_all_data_sources,
    'interval',
    hours=6,
    id='sync_data'
)

# Batch predictions - every hour
scheduler.add_job(
    run_batch_predictions,
    'cron',
    minute=0,
    id='batch_predict'
)

# Model drift check - daily
scheduler.add_job(
    check_model_drift,
    'cron',
    hour=3,
    minute=30,
    id='check_drift'
)

scheduler.start()
```

---

## Step 5: Nginx Reverse Proxy

Configure Nginx to handle both frontend and API:

```nginx
# /etc/nginx/sites-available/forecastx
upstream forecastx_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name forecastx.com *.forecastx.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name forecastx.com *.forecastx.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/forecastx.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/forecastx.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/forecastx-access.log combined;
    error_log /var/log/nginx/forecastx-error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # API requests
    location /api/ {
        proxy_pass http://forecastx_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support (for real-time updates)
    location /ws/ {
        proxy_pass http://forecastx_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Frontend static files
    location / {
        root /var/www/forecastx/html;
        try_files $uri $uri/ /index.html;
        
        # Cache control for index.html
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
        
        # Cache control for other files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            add_header Cache-Control "public, max-age=31536000, immutable";
        }
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://forecastx_backend/health;
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/forecastx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 6: SSL Certificates

### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx \
  -d forecastx.com \
  -d app.forecastx.com \
  -d api.forecastx.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Verify renewal
sudo certbot renew --dry-run
```

---

## Step 7: Monitoring & Logging

### Application Logging

```python
# backend/app/config.py
import logging
from pythonjsonlogger import jsonlogger

# JSON logging for structured logs
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### Prometheus Metrics

```bash
# Install Prometheus client
pip install prometheus-client

# Add to FastAPI app
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

request_count = Counter('forecastx_requests_total', 'Total requests')
request_duration = Histogram('forecastx_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    with request_duration.time():
        request_count.inc()
        response = await call_next(request)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Sentry Error Tracking

```bash
pip install sentry-sdk

# In main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1
)
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.yml for ELK
version: '3'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    ports:
      - "5000:5000"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## Step 8: Database Backups

### Automated Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-forecastx-db.sh

BACKUP_DIR="/backups/forecastx"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -U forecastx_user \
  -d forecastx_prod \
  -F c \
  -f "$BACKUP_DIR/forecastx_$DATE.dump"

# Compress
gzip "$BACKUP_DIR/forecastx_$DATE.dump"

# Upload to S3
aws s3 cp "$BACKUP_DIR/forecastx_$DATE.dump.gz" \
  s3://forecastx-backups/ \
  --storage-class GLACIER

# Keep only last 7 days locally
find $BACKUP_DIR -name "forecastx_*.dump.gz" -mtime +7 -delete

echo "Backup completed: forecastx_$DATE.dump.gz"
```

Setup cron job:

```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-forecastx-db.sh >> /var/log/forecastx-backup.log 2>&1
```

### Restore from Backup

```bash
# Download from S3
aws s3 cp s3://forecastx-backups/forecastx_20260822_020000.dump.gz .
gunzip forecastx_20260822_020000.dump.gz

# Restore
pg_restore -U forecastx_user \
  -d forecastx_prod \
  -v forecastx_20260822_020000.dump
```

---

## Step 9: Docker Deployment (Optional)

### Docker Compose for Full Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: forecastx_prod
      POSTGRES_USER: forecastx_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://forecastx_user:${DB_PASSWORD}@postgres:5432/forecastx_prod
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks worker -l info
    environment:
      DATABASE_URL: postgresql://forecastx_user:${DB_PASSWORD}@postgres:5432/forecastx_prod
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Build and run:

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## Step 10: Testing Before Production

### Pre-Deployment Testing

```bash
# Run all tests
pytest backend/tests -v --cov=app --cov-report=html

# Run security checks
bandit -r backend/app

# Check dependencies for vulnerabilities
safety check

# Lint code
flake8 backend/app
black --check backend/app
pylint backend/app

# Type checking
mypy backend/app
```

### Smoke Tests

```python
# backend/tests/smoke_test.py
import requests

API_URL = "https://api.forecastx.com"

def test_api_health():
    """Test API is responding"""
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200

def test_database_connection():
    """Test database connection"""
    response = requests.get(f"{API_URL}/health/db")
    assert response.status_code == 200

def test_redis_connection():
    """Test Redis connection"""
    response = requests.get(f"{API_URL}/health/redis")
    assert response.status_code == 200

def test_auth_flow():
    """Test authentication"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    assert response.status_code in [200, 401]
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f locustfile.py --host=https://api.forecastx.com
```

---

## Step 11: Production Deployment

### Deployment Checklist

```bash
# 1. Create backup
pg_dump -U forecastx_user forecastx_prod > backup_pre_deploy.sql

# 2. Pull latest code
git fetch origin
git checkout v1.0.0

# 3. Run migrations
alembic upgrade head

# 4. Run tests
pytest backend/tests -v

# 5. Rebuild frontend
cd frontend && npm install && npm run build

# 6. Deploy frontend
aws s3 sync build/ s3://forecastx-frontend-prod --delete

# 7. Restart backend services
sudo systemctl restart forecastx-api
sudo systemctl restart forecastx-worker

# 8. Verify deployment
curl https://api.forecastx.com/health
curl https://forecastx.com/

# 9. Run smoke tests
pytest backend/tests/smoke_test.py -v

# 10. Monitor logs
tail -f /var/log/forecastx/app.log
tail -f /var/log/nginx/forecastx-access.log
```

### Blue-Green Deployment

For zero-downtime deploys:

```bash
# Green = new version, Blue = current version

# 1. Deploy to "green" servers (new instances)
docker pull your-registry/forecastx-backend:1.1.0
docker run -d --name forecastx-green \
  -p 8002:8000 \
  your-registry/forecastx-backend:1.1.0

# 2. Health check green
curl http://localhost:8002/health

# 3. Switch load balancer to green
# Update Nginx upstream to point to green

# 4. Verify traffic flows correctly
# 5. Keep blue running for 1 hour as rollback
# 6. Shut down blue after verification
docker stop forecastx-blue
```

---

## Step 12: Monitoring & Alerting

### Key Metrics to Monitor

```
- API response time (p50, p95, p99)
- Error rate (5xx errors per minute)
- Database connection pool utilization
- Redis memory usage
- Model training duration
- Sync job success rate
- Worker queue depth
- SSL certificate expiry
```

### Alert Rules Example (Prometheus)

```yaml
groups:
  - name: forecastx_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(forecastx_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, forecastx_request_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "High API latency detected"

      - alert: DatabaseConnectionPoolFull
        expr: forecastx_db_connections / forecastx_db_max_connections > 0.9
        for: 5m
        annotations:
          summary: "Database connection pool nearly full"
```

---

## Step 13: Rollback Procedure

If deployment fails:

```bash
# 1. Identify issue
tail -f /var/log/forecastx/app.log

# 2. Revert code
git checkout v1.0.0

# 3. Rebuild frontend
cd frontend && npm run build

# 4. Redeploy frontend
aws s3 sync build/ s3://forecastx-frontend-prod

# 5. Restart backend
sudo systemctl restart forecastx-api
sudo systemctl restart forecastx-worker

# 6. If database issue, restore backup
psql -U forecastx_user forecastx_prod < backup_pre_deploy.sql

# 7. Verify
curl https://api.forecastx.com/health
```

---

## Step 14: Post-Deployment Verification

### Week 1

- Monitor error rates (target: < 0.1%)
- Track API latency (target: < 500ms p95)
- Monitor database performance
- Check worker queue depth
- Verify all integrations working
- Review logs for warnings
- Monitor resource usage

### Week 2-4

- Performance analysis
- User feedback collection
- Fix any issues found
- Optimize slow queries
- Update documentation
- Plan next release

---

## Troubleshooting

### Common Issues & Fixes

**Issue: API won't start**
```bash
# Check for syntax errors
python -m py_compile app/main.py

# Verify environment variables
env | grep DATABASE_URL

# Check database connection
python -c "from app.db.database import engine; engine.connect()"
```

**Issue: High memory usage**
```bash
# Check for memory leaks
ps aux | grep python
# Monitor Redis
redis-cli INFO memory

# Restart worker if needed
sudo systemctl restart forecastx-worker
```

**Issue: Database queries slow**
```bash
# Check slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

# Add indexes if needed
CREATE INDEX idx_predictions_score ON predictions(score);

# Analyze query plan
EXPLAIN ANALYZE SELECT * FROM customers WHERE status = 'active';
```

---

## Summary Checklist

- [ ] Database created and migrations run
- [ ] Backend configured and running
- [ ] Frontend built and deployed
- [ ] Workers configured
- [ ] Nginx reverse proxy configured
- [ ] SSL certificates installed
- [ ] Logging and monitoring set up
- [ ] Backups configured
- [ ] All tests passing
- [ ] Pre-deployment checks completed
- [ ] Deployment executed
- [ ] Smoke tests passed
- [ ] Monitoring active
- [ ] Team notified

---

## Support & Documentation

**API Documentation**: `https://api.forecastx.com/docs`
**Health Check**: `https://api.forecastx.com/health`
**Admin Console**: `https://forecastx.com/admin`
**Logs**: `/var/log/forecastx/`
**Database**: `forecastx_prod` on PostgreSQL

For issues, refer to:
- Application logs: `/var/log/forecastx/app.log`
- Nginx logs: `/var/log/nginx/forecastx-*.log`
- Database logs: `/var/log/postgresql/`
- Sentry: `https://sentry.io` (if enabled)

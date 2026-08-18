# 🚀 PredictX Quick Start Guide

## 5-Minute Local Setup

```bash
# 1. Clone & enter directory
git clone https://github.com/zaptapagency/predictx.git
cd predictx

# 2. Setup credentials (follow CREDENTIALS_SETUP.md for details)
export DATABASE_URL='postgresql://predictx:password@localhost:5432/predictx'
export REDIS_URL='redis://localhost:6379'
export JWT_SECRET_KEY='$(openssl rand -base64 48)'
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USER='your-email@gmail.com'
export SMTP_PASSWORD='your-16-char-app-password'
export STRIPE_API_KEY='sk_test_...'
export STRIPE_WEBHOOK_SECRET='whsec_...'
export STRIPE_PRO_PRICE_ID='price_...'
export STRIPE_ENTERPRISE_PRICE_ID='price_...'
export FRONTEND_URL='http://localhost:3000'

# 3. Run automated setup
./setup-credentials-auto.sh

# 4. Deploy locally
./deploy.sh

# 5. Test everything
./test-deployment.sh
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Production Deployment (Railway)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add PostgreSQL plugin
railway add postgres

# 5. Set environment variables
railway variable set DATABASE_URL=...
railway variable set STRIPE_API_KEY=...
# ... set all other variables

# 6. Deploy
railway up

# 7. Get URL
railway domains
```

---

## Production Deployment (DigitalOcean)

```bash
# 1. Create droplet
doctl compute droplet create predictx --image docker-20-04 --size s-2vcpu-4gb

# 2. SSH and setup
ssh root@your-ip
apt-get update && apt-get install -y docker.io docker-compose

# 3. Deploy
git clone https://github.com/zaptapagency/predictx.git
cd predictx
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
docker-compose exec backend alembic upgrade head

# 4. Configure Nginx & SSL (see DEPLOYMENT.md)
```

---

## Complete Documentation

- **[CREDENTIALS_SETUP.md](./CREDENTIALS_SETUP.md)** - Detailed credential setup
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Full deployment guide
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist
- **[SAAS_PLATFORM_GUIDE.md](./SAAS_PLATFORM_GUIDE.md)** - Architecture & features
- **[BUILD_SUMMARY.md](./BUILD_SUMMARY.md)** - What was built

---

## Automation Scripts

```bash
./setup-credentials-auto.sh  # Automated credential setup
./deploy.sh                  # Deploy with Docker Compose
./test-deployment.sh         # Comprehensive test suite
./setup-monitoring.sh        # Setup monitoring & logging
```

---

## Key Endpoints

**Authentication:**
- `POST /api/auth/signup` - Register
- `POST /api/auth/login` - Login
- `POST /api/auth/password-reset` - Reset password

**User:**
- `GET /api/users/me` - Get profile
- `PUT /api/users/me` - Update profile

**Predictions:**
- `POST /api/predictions` - Make prediction
- `GET /api/predictions/history` - Get history

**Subscriptions:**
- `GET /api/subscriptions/current` - Current subscription
- `POST /api/subscriptions/upgrade` - Upgrade

**Admin:**
- `GET /api/admin/users` - List users
- `GET /api/admin/analytics` - Analytics

---

## Database

**PostgreSQL 15**
- Connection: localhost:5432
- User: predictx
- Database: predictx
- Migrations: `docker-compose exec backend alembic upgrade head`

**Redis 7**
- Connection: localhost:6379
- Used for: caching, rate limiting, sessions

---

## Monitoring & Logs

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Health check
curl http://localhost:8000/health

# Database status
docker-compose exec postgres psql -U predictx -d predictx -c "SELECT 1"
```

---

## Support

- **GitHub**: https://github.com/zaptapagency/predictx
- **Email**: support@predictx.com
- **API Docs**: http://localhost:8000/docs


# 🚀 PredictX Deployment Guide

## Quick Start (Local Docker)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
nano .env

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Access the application
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
```

---

## Production Deployment

### Option 1: Railway (Recommended)

#### Backend Deployment

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Create new project
railway init

# 4. Create PostgreSQL plugin
railway add postgres

# 5. Set environment variables
railway variable set STRIPE_API_KEY=sk_live_...
railway variable set JWT_SECRET_KEY=your-secret
railway variable set STRIPE_WEBHOOK_SECRET=whsec_...
# ... add all other variables

# 6. Deploy backend
railway up

# 7. Get backend URL
railway domains
```

#### Frontend Deployment (Vercel)

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy frontend
cd frontend
vercel

# 4. Set environment variable
vercel env add REACT_APP_API_URL https://your-railway-backend.railway.app

# 5. Redeploy with env
vercel --prod
```

---

### Option 2: DigitalOcean

#### Step 1: Create Droplet

```bash
# Create Docker droplet (8GB RAM recommended)
doctl compute droplet create predictx \
  --image docker-20-04 \
  --size s-2vcpu-4gb \
  --region nyc3 \
  --enable-monitoring
```

#### Step 2: SSH into Droplet

```bash
ssh root@your-droplet-ip
```

#### Step 3: Install Dependencies

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker & Docker Compose
apt-get install -y docker.io docker-compose

# Add current user to docker group
usermod -aG docker $USER
```

#### Step 4: Deploy Application

```bash
# Clone repository
git clone https://github.com/zaptapagency/predictx.git
cd predictx

# Copy and edit environment
cp .env.example .env
nano .env

# Start services
docker-compose -f docker-compose.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

#### Step 5: Setup Nginx Reverse Proxy

```bash
# Install Nginx
apt-get install -y nginx

# Create config
cat > /etc/nginx/sites-available/predictx << 'NGINX'
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX

# Enable site
ln -s /etc/nginx/sites-available/predictx /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 6: Setup SSL (Let's Encrypt)

```bash
apt-get install -y certbot python3-certbot-nginx

certbot --nginx -d your-domain.com
```

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/predictx

# Redis
REDIS_URL=redis://host:6379

# JWT
JWT_SECRET_KEY=your-64-char-random-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# SMTP (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password

# Stripe
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# URLs
FRONTEND_URL=https://predictx.com

# LightGBM
LIGHTGBM_REPO_URL=https://github.com/...
LIGHTGBM_REPO_BRANCH=main

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend (.env)

```env
REACT_APP_API_URL=https://api.predictx.com
```

---

## Database Setup

### PostgreSQL

```bash
# Connect to database
psql postgresql://user:pass@host:5432/predictx

# Run migrations
alembic upgrade head

# Verify tables
\dt
```

### Redis

```bash
# Check Redis connection
redis-cli ping
# Expected: PONG
```

---

## Stripe Webhook Setup

1. Go to Stripe Dashboard
2. Settings → Webhooks
3. Add endpoint: `https://your-domain.com/api/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded`
5. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

---

## Email Service Setup (Gmail)

1. Enable 2FA in Google Account
2. Generate app password:
   - Account → Security → App passwords
   - Select Mail and Windows Computer
   - Copy 16-char password to `SMTP_PASSWORD`

---

## Monitoring & Logging

### Docker Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs
```

---

## Scaling

### Increase Resources

```bash
# Railway
railway variable set RAILWAY_MEMORY=2GB

# DigitalOcean
doctl compute droplet resize predictx --size s-4vcpu-8gb
```

### Database Backups

```bash
# PostgreSQL backup
pg_dump postgresql://user:pass@host/predictx > backup.sql

# Restore backup
psql postgresql://user:pass@host/predictx < backup.sql
```

---

## Troubleshooting

### Backend Connection Error
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check logs
docker-compose logs backend
```

### Database Connection Error
```bash
# Check PostgreSQL
docker-compose exec postgres psql -U predictx -d predictx -c "SELECT 1"
```

### Frontend Not Loading
```bash
# Clear cache and restart
docker-compose restart frontend
```

### Stripe Webhook Issues
```bash
# Check webhook logs in Stripe Dashboard
# Test webhook: curl -X POST http://localhost:8000/api/webhooks/stripe \
#   -H "Content-Type: application/json" \
#   -d '{"type": "customer.subscription.created"}'
```

---

## Performance Optimization

1. **Enable caching** - Use Redis for session storage
2. **Database indexing** - Already included in migrations
3. **CDN** - Put frontend behind CloudFlare CDN
4. **Compression** - Enable gzip in Nginx
5. **Rate limiting** - Enabled on all endpoints

---

## Security Checklist

- [x] HTTPS enforced
- [x] CORS configured
- [x] Rate limiting enabled
- [x] Input validation
- [x] SQL injection prevention (ORM)
- [x] XSS prevention
- [x] Password hashing (bcrypt)
- [x] API key hashing
- [x] Webhook verification
- [ ] WAF configured
- [ ] DDoS protection
- [ ] Regular backups scheduled

---

## Support

- API Docs: `https://your-domain.com/docs`
- GitHub: https://github.com/zaptapagency/predictx
- Email: support@predictx.com


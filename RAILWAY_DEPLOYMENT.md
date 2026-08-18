# 🚀 PredictX Railway Deployment Guide

## Overview

Railway is the easiest way to deploy PredictX. It handles infrastructure, SSL, databases, and auto-scaling.

**Time to Deploy: 30 minutes**

---

## Prerequisites

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Create Railway Account

Go to https://railway.app and sign up (free tier available)

### 3. Collect Credentials

Before deploying, gather:
- [ ] SMTP credentials (Gmail app password)
- [ ] Stripe API keys (sk_live_...)
- [ ] Stripe webhook secret
- [ ] Stripe price IDs (Pro & Enterprise)
- [ ] JWT secret key (run: `openssl rand -base64 48`)
- [ ] Frontend URL (your domain)

---

## Automated Deployment (Recommended)

```bash
# Run the automated deployment script
./deploy-railway.sh
```

This will:
1. ✅ Login to Railway
2. ✅ Create new project
3. ✅ Add PostgreSQL database
4. ✅ Configure environment variables
5. ✅ Deploy backend
6. ✅ Run migrations
7. ✅ Verify deployment

---

## Manual Deployment Steps

### Step 1: Login to Railway

```bash
railway login
```

Opens browser for authentication. Click "Authorize" when prompted.

### Step 2: Initialize Project

```bash
railway init
```

Creates `.railway/config.json` in your project.

### Step 3: Add PostgreSQL Database

```bash
railway add postgres
```

This adds PostgreSQL plugin and generates `DATABASE_URL` automatically.

### Step 4: Deploy Backend

```bash
railway up
```

Deploys code to Railway. First deployment takes 2-3 minutes.

### Step 5: Set Environment Variables

```bash
# Get database URL from PostgreSQL plugin
railway variable set DATABASE_URL='postgresql://...'

# Redis (optional - for production use Redis Cloud)
railway variable set REDIS_URL='redis://localhost:6379'

# JWT
railway variable set JWT_SECRET_KEY='your-64-char-key'

# Email (SMTP)
railway variable set SMTP_SERVER='smtp.gmail.com'
railway variable set SMTP_PORT='587'
railway variable set SMTP_USER='your-email@gmail.com'
railway variable set SMTP_PASSWORD='your-16-char-app-password'

# Stripe
railway variable set STRIPE_API_KEY='sk_live_...'
railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'
railway variable set STRIPE_PRO_PRICE_ID='price_...'
railway variable set STRIPE_ENTERPRISE_PRICE_ID='price_...'

# Frontend
railway variable set FRONTEND_URL='https://your-domain.com'

# Environment
railway variable set ENVIRONMENT='production'
railway variable set DEBUG='false'
```

### Step 6: Run Database Migrations

```bash
railway run alembic upgrade head
```

Creates all database tables and runs migrations.

### Step 7: Get Backend URL

```bash
railway domains
```

Shows your backend URL (e.g., `https://predictx-backend-production.railway.app`)

### Step 8: Verify Deployment

```bash
# Check health
curl https://predictx-backend-production.railway.app/health

# View logs
railway logs

# Check status
railway status
```

---

## Environment Variables Explained

| Variable | Example | Source |
|----------|---------|--------|
| DATABASE_URL | `postgresql://...` | Railway PostgreSQL |
| REDIS_URL | `redis://...` | Redis Cloud |
| JWT_SECRET_KEY | 64-char random | `openssl rand -base64 48` |
| SMTP_SERVER | `smtp.gmail.com` | Gmail |
| SMTP_PORT | `587` | Gmail |
| SMTP_USER | `your@gmail.com` | Your email |
| SMTP_PASSWORD | 16-char app password | Gmail app passwords |
| STRIPE_API_KEY | `sk_live_...` | Stripe dashboard |
| STRIPE_WEBHOOK_SECRET | `whsec_...` | Stripe webhooks |
| STRIPE_PRO_PRICE_ID | `price_...` | Stripe products |
| STRIPE_ENTERPRISE_PRICE_ID | `price_...` | Stripe products |
| FRONTEND_URL | `https://your-domain` | Your domain |
| ENVIRONMENT | `production` | Fixed value |
| DEBUG | `false` | Fixed value |

---

## Useful Railway Commands

```bash
# Login/Logout
railway login
railway logout

# Project management
railway init                 # Initialize project
railway link                 # Link to existing project
railway status              # Show project status

# Variables
railway variable set KEY=VALUE
railway variable list
railway variable delete KEY

# Deployment
railway up                  # Deploy current branch
railway logs -f             # Follow logs in real-time
railway shell              # SSH into running service

# Domains
railway domains            # List your URLs
railway domain add         # Add custom domain

# Database
railway variable get DATABASE_URL  # Get DB connection string
```

---

## Production Setup

### 1. Custom Domain

```bash
railway domain add your-domain.com
```

Add DNS record:
- Type: CNAME
- Name: `api`
- Value: `<railway-url>`

### 2. SSL Certificate

Railway automatically provisions Let's Encrypt SSL. No additional setup needed.

### 3. Redis for Production

For production, use Redis Cloud:

1. Go to https://redis.com/try-free
2. Create database
3. Copy connection string
4. Set: `railway variable set REDIS_URL='redis://...'`

### 4. Monitoring

Railway dashboard shows:
- Deployment status
- Logs in real-time
- CPU/Memory usage
- Database performance

---

## Frontend Deployment (Vercel)

After backend is deployed:

```bash
# Install Vercel CLI
npm i -g vercel

# Go to frontend directory
cd frontend

# Deploy
vercel --prod

# Set API URL to your Railway backend
vercel env add REACT_APP_API_URL https://your-backend-url

# Redeploy with environment
vercel --prod
```

---

## Stripe Webhook Setup

After backend URL is known:

1. Go to Stripe Dashboard
2. Settings → Webhooks
3. Add endpoint: `https://your-backend-url/api/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded`
5. Copy webhook secret
6. Set: `railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'`

---

## Testing After Deployment

```bash
# 1. Check health
curl https://your-backend-url/health

# 2. View API docs
open https://your-backend-url/docs

# 3. Test signup
curl -X POST https://your-backend-url/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123",
    "full_name": "Test User"
  }'

# 4. Check logs
railway logs -f

# 5. View database
railway variable get DATABASE_URL
# Use psql or DBeaver to connect and verify tables
```

---

## Troubleshooting

### Deployment Failed

```bash
# Check logs
railway logs

# View recent deployments
railway logs --service backend

# Re-run deployment
railway up
```

### Database Connection Error

```bash
# Verify DATABASE_URL is set
railway variable get DATABASE_URL

# Test connection
railway run psql $DATABASE_URL -c "SELECT 1"
```

### Migrations Not Running

```bash
# Run manually
railway run alembic upgrade head

# Check migration status
railway run alembic current
```

### Email Not Sending

```bash
# Verify SMTP credentials
railway variable list | grep SMTP

# Check logs for errors
railway logs | grep -i email
```

### Payment Not Working

```bash
# Verify Stripe keys
railway variable list | grep STRIPE

# Check Stripe webhook in dashboard
# View webhook delivery logs
```

---

## Monitoring & Logs

### Real-Time Logs

```bash
railway logs -f
```

### Filter Logs

```bash
# Show only errors
railway logs | grep ERROR

# Show only API requests
railway logs | grep "POST\|GET\|PUT\|DELETE"

# Follow specific service
railway logs -f --service backend
```

### Database Monitoring

```bash
# Connect to database
railway run psql -c "SELECT COUNT(*) FROM users"

# Check table sizes
railway run psql -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables;"

# View active connections
railway run psql -c "SELECT * FROM pg_stat_activity;"
```

---

## Scaling & Performance

### Increase Resources

Go to Railway Dashboard → Settings → Plan

Options:
- Basic: Free
- Pro: $5+/month
- Business: Custom

### Auto-Scaling

Railway automatically scales based on:
- CPU usage
- Memory usage
- Request load

Monitor in Dashboard → Deployments → Metrics

---

## Cost Estimation

| Component | Free Tier | Pro Tier |
|-----------|-----------|----------|
| Backend (1 GB RAM) | Included | Included |
| PostgreSQL (5 GB) | Included | $7/month |
| Outbound (100 GB) | Included | Included |
| **Total** | Free | ~$7/month |

**Note:** Pro features required for production:
- Custom domains
- Multiple services
- Database backups

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Status Page**: https://status.railway.app
- **Discord**: https://discord.gg/railway
- **Email**: support@railway.app

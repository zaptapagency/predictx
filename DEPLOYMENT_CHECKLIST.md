# 🚀 PredictX Deployment Checklist

## Pre-Deployment (Day 1-2)

### 1. Local Development Setup
- [ ] Clone repository: `git clone https://github.com/zaptapagency/predictx.git`
- [ ] Setup credentials: `./setup-credentials.sh`
- [ ] Start local deployment: `./deploy.sh`
- [ ] Verify services: `./test-deployment.sh`

### 2. Backend Configuration
- [ ] Database URL (PostgreSQL)
- [ ] Redis URL
- [ ] JWT Secret Key: `openssl rand -base64 48`
- [ ] SMTP Configuration (Gmail app password)

### 3. Stripe Setup
- [ ] Create Stripe account at https://stripe.com
- [ ] Get API keys (sk_live_...)
- [ ] Get Webhook Secret (whsec_...)
- [ ] Create pricing plans (Free, Pro, Enterprise)
- [ ] Get Price IDs for Pro and Enterprise
- [ ] Add webhook endpoint: `https://your-domain.com/api/webhooks/stripe`

### 4. Domain & SSL
- [ ] Purchase domain
- [ ] Setup DNS records (A record to server IP)
- [ ] Setup SSL with Let's Encrypt (automatic with Certbot)

---

## Deployment (Day 2-3)

### 5. Backend Deployment (Railway)
```bash
npm install -g @railway/cli
railway login
railway init
railway add postgres
railway variable set DATABASE_URL=...
railway variable set STRIPE_API_KEY=...
railway up
railway domains
```

### 6. Backend Deployment (DigitalOcean)
```bash
doctl compute droplet create predictx --image docker-20-04 --size s-2vcpu-4gb
ssh root@ip
apt-get update && apt-get install -y docker.io docker-compose
git clone https://github.com/zaptapagency/predictx.git
cd predictx
cp .env.example .env
# Edit .env
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### 7. Frontend Deployment (Vercel)
```bash
npm i -g vercel
vercel login
cd frontend
vercel --prod
vercel env add REACT_APP_API_URL https://api.your-domain.com
vercel --prod
```

### 8. Database Migrations
- [ ] Migrations successful: `docker-compose exec backend alembic current`
- [ ] All tables created: `docker-compose exec postgres psql -U predictx -d predictx -c "\dt"`

---

## Testing (Day 3)

### 9. User Flow Testing
- [ ] **Signup** → email verification → login
- [ ] **Dashboard** → usage stats display
- [ ] **Predictions** → model selection → results → history
- [ ] **Billing** → upgrade to Pro → Stripe test payment (4242 4242 4242 4242)
- [ ] **API Keys** → create, copy, use, revoke
- [ ] **Admin** → dashboard, user management, analytics

### 10. API Testing
```bash
curl https://your-domain.com/health
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

### 11. Email Testing
- [ ] Verification email received after signup
- [ ] Password reset email received
- [ ] Invoice email received after payment

### 12. Security Testing
- [ ] HTTPS enforced (no HTTP redirect)
- [ ] API requires authentication
- [ ] Rate limiting active
- [ ] CORS working correctly

---

## Post-Deployment (Day 4+)

### 13. Monitoring Setup
```bash
./setup-monitoring.sh
```
- [ ] Sentry configured for error tracking
- [ ] UptimeRobot monitoring enabled
- [ ] Log aggregation setup
- [ ] Performance monitoring active

### 14. Backup Setup
- [ ] Daily PostgreSQL backups scheduled
- [ ] Backup retention policy (30 days)
- [ ] Test restore from backup

### 15. Documentation
- [ ] README updated with production URLs
- [ ] Admin runbook created
- [ ] Support procedures documented
- [ ] Status page setup (StatusPage.io)

### 16. Launch
- [ ] All tests passing
- [ ] Monitoring active
- [ ] Support team trained
- [ ] Runbook created
- [ ] Ready for traffic

---

## Success Metrics (First Week)
- ✅ 0 critical errors
- ✅ 99.9% uptime
- ✅ <200ms API response
- ✅ 100% email delivery
- ✅ Payment processing working

## Troubleshooting Commands
```bash
# Check backend logs
docker-compose logs -f backend

# Check database
docker-compose exec postgres psql -U predictx -d predictx -c "SELECT 1"

# Check API health
curl https://your-domain.com/health

# Test Stripe
grep STRIPE .env

# Test SMTP
grep SMTP .env
```

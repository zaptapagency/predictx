# 🎯 PredictX Complete Deployment Plan

Master guide for deploying PredictX from start to finish. Follow this plan to take your SaaS platform from local development to production.

---

## Phase 1: Pre-Deployment (Day 1)

### 1.1 Verify Local Setup ✅
```bash
# Clone and setup locally
git clone https://github.com/zaptapagency/predictx.git
cd predictx

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or ''.\\venv\\Scripts\\activate'' on Windows
pip install -r requirements.txt
cp .env.example .env

# Frontend setup
cd ../frontend
npm install
npm start
```

### 1.2 Create Accounts
- [ ] Railway: https://railway.app (sign up)
- [ ] Vercel: https://vercel.com (sign up)
- [ ] Stripe: https://stripe.com (sign up)
- [ ] Gmail: Enable 2FA for app passwords

### 1.3 Gather Credentials (Use CREDENTIALS_SETUP.md)
- [ ] Database URL (PostgreSQL)
- [ ] Redis URL
- [ ] JWT Secret Key (`openssl rand -base64 48`)
- [ ] SMTP credentials (Gmail app password)
- [ ] Stripe API keys
- [ ] Stripe webhook secret
- [ ] Stripe price IDs
- [ ] Frontend/Backend URLs

**Reference**: See `CREDENTIALS_SETUP.md` for detailed steps

---

## Phase 2: Backend Deployment (Day 2)

### 2.1 Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Add PostgreSQL
railway add postgres

# Add Redis (optional)
railway add redis

# Deploy
railway up

# View logs
railway logs -f
```

### 2.2 Configure Environment Variables

```bash
# Database (auto from Railway PostgreSQL)
railway variable set DATABASE_URL='...'

# Redis
railway variable set REDIS_URL='...'

# JWT
railway variable set JWT_SECRET_KEY='...'

# Email (SMTP)
railway variable set SMTP_SERVER='smtp.gmail.com'
railway variable set SMTP_PORT='587'
railway variable set SMTP_USER='your@gmail.com'
railway variable set SMTP_PASSWORD='...'

# Stripe
railway variable set STRIPE_API_KEY='sk_live_...'
railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'
railway variable set STRIPE_PRO_PRICE_ID='price_...'
railway variable set STRIPE_ENTERPRISE_PRICE_ID='price_...'

# Frontend
railway variable set FRONTEND_URL='https://your-frontend.com'

# Environment
railway variable set ENVIRONMENT='production'
railway variable set DEBUG='false'
```

### 2.3 Run Database Migrations

```bash
# Run migrations
railway run alembic upgrade head

# Verify tables created
railway run psql -c "\\dt"

# Verify data
railway run psql -c "SELECT COUNT(*) FROM users"
```

### 2.4 Get Backend URL

```bash
railway domains
# Copy: predictx-backend-production.railway.app
```

### 2.5 Verify Backend

```bash
# Health check
curl https://predictx-backend-production.railway.app/health

# API docs
https://predictx-backend-production.railway.app/docs

# Test signup
curl -X POST https://predictx-backend-production.railway.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d ''{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123",
    "full_name": "Test User"
  }''
```

**Reference**: See `RAILWAY_DEPLOYMENT.md` for detailed steps

---

## Phase 3: Frontend Deployment (Day 2)

### 3.1 Setup Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy frontend
cd frontend
vercel --prod
```

### 3.2 Configure Frontend Environment

```bash
# Set API URL
vercel env add REACT_APP_API_URL
# Enter: https://predictx-backend-production.railway.app

# Redeploy
vercel --prod
```

### 3.3 Verify Frontend

```bash
# Open in browser
https://your-project.vercel.app

# Test signup flow
1. Click Sign Up
2. Enter email, username, password
3. Verify email
4. Login
5. View dashboard
```

### 3.4 Update Backend Configuration

```bash
# Get Vercel URL
# Go to: https://vercel.com/dashboard → your-project
# Copy URL

# Update Railway
railway variable set FRONTEND_URL='https://your-project.vercel.app'
```

---

## Phase 4: Stripe Setup (Day 2)

### 4.1 Configure Stripe Webhook

1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Set URL: `https://predictx-backend-production.railway.app/api/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded`
5. Click "Add endpoint"
6. Copy signing secret

### 4.2 Set Webhook Secret

```bash
railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'

# Verify webhook
railway logs | grep webhook
```

---

## Phase 5: Testing (Day 3)

### 5.1 User Flow Testing

```bash
# 1. Signup
https://your-frontend.com/signup
- Email: test@example.com
- Username: testuser
- Password: TestPassword123

# 2. Verify Email
- Check email
- Click verification link

# 3. Login
https://your-frontend.com/login
- Email: test@example.com
- Password: TestPassword123

# 4. Dashboard
- View usage stats
- See subscription tier
- Access predictions

# 5. Billing
- Upgrade to Pro
- Enter test card: 4242 4242 4242 4242
- Any expiry, any CVC
- Verify subscription activated

# 6. API Keys
- Create API key
- Copy key
- Use in API request

# 7. Admin (if admin)
- Go to /admin
- View dashboard
- Check users
- View subscriptions
```

### 5.2 API Testing

```bash
# Test health
curl https://your-backend.com/health

# Test signup
curl -X POST https://your-backend.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d ''{...}''

# Test login
curl -X POST https://your-backend.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d ''{...}''

# Test predictions
curl -X POST https://your-backend.com/api/predictions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d ''{...}''
```

### 5.3 Email Testing

- [ ] Verification email received after signup
- [ ] Password reset email works
- [ ] Invoice email sent after payment
- [ ] Check spam folder if missing

### 5.4 Security Testing

- [ ] HTTPS enforced (no HTTP)
- [ ] CORS working correctly
- [ ] API requires authentication
- [ ] Rate limiting active
- [ ] Invalid tokens rejected

**Reference**: See `DEPLOYMENT_CHECKLIST.md` for testing checklist

---

## Phase 6: Monitoring Setup (Day 3)

### 6.1 Enable Logging

```bash
# Follow logs
railway logs -f

# Filter errors
railway logs | grep ERROR

# Archive logs
railway logs > production.log
```

### 6.2 Setup Health Checks

```bash
# Use UptimeRobot
1. Go to https://uptimerobot.com
2. Add monitor: https://your-backend.com/health
3. Alert on downtime
4. Check every 5 minutes
```

### 6.3 Monitor Metrics

**Railway Dashboard**:
- Deployments
- CPU/Memory usage
- Database connections
- Error rates

**Vercel Dashboard**:
- Build times
- Web Vitals
- Analytics
- Error tracking

**Stripe Dashboard**:
- Payment success rate
- Failed payments
- Revenue metrics
- Webhook deliveries

**Reference**: See `MONITORING_GUIDE.md` for detailed monitoring

---

## Phase 7: Production Hardening (Day 4)

### 7.1 Security

```bash
# Rotate secrets
openssl rand -base64 48  # New JWT secret
railway variable set JWT_SECRET_KEY='...'

# Enable HTTPS
# Railway auto-provisions Let's Encrypt - Already enabled

# Review CORS
# Check backend/app/main.py CORS settings

# Rate limiting
# Check: backend/app/api/auth.py for rate limit headers
```

### 7.2 Backups

```bash
# Manual PostgreSQL backup
railway run pg_dump -Fc > backup.dump

# Schedule backups
# Railway: Settings → Backups (auto-enabled)
```

### 7.3 Custom Domain (Optional)

```bash
# Purchase domain (namecheap, godaddy, etc.)

# Railway Custom Domain
railway domain add your-domain.com

# Vercel Custom Domain
# Dashboard → Settings → Domains → Add

# DNS Records
# CNAME: api → your-railway-url
# CNAME: @ → your-vercel-url
```

---

## Phase 8: Launch (Day 5)

### 8.1 Final Verification

- [ ] Backend responding at production URL
- [ ] Frontend loading and accessible
- [ ] Database connected and migrated
- [ ] Email sending verified
- [ ] Stripe webhooks working
- [ ] Payment flow tested
- [ ] Monitoring active
- [ ] Backups enabled
- [ ] Error tracking setup
- [ ] Health checks enabled

### 8.2 Announce Launch

```bash
# Update README
git add README.md
git commit -m "Update deployment URLs"
git push

# Post on social media
# Email users
# Start marketing
```

### 8.3 Post-Launch Monitoring

```bash
# First 24 hours: Check every hour
railway logs -f

# First week: Check daily
railway logs | grep ERROR

# Monitor Stripe
dashboard.stripe.com → Webhooks → Logs

# Monitor frontend
vercel.com → Dashboard → Analytics
```

---

## Reference Guides

### Quick Navigation
- **5-minute quick start**: `QUICK_START.md`
- **Credential setup**: `CREDENTIALS_SETUP.md`
- **Railway details**: `RAILWAY_DEPLOYMENT.md`
- **Monitoring & troubleshooting**: `MONITORING_GUIDE.md`
- **Deployment checklist**: `DEPLOYMENT_CHECKLIST.md`

### Key Commands

**Railway**:
```bash
railway login
railway init
railway up
railway logs -f
railway variable set KEY=VALUE
railway run psql -c "SELECT 1"
```

**Vercel**:
```bash
vercel login
vercel --prod
vercel env add KEY
```

**Database**:
```bash
railway run alembic upgrade head
railway run psql -c "SELECT 1"
railway run pg_dump > backup.dump
```

---

## Timeline

| Phase | Duration | Days | Cumulative |
|-------|----------|------|-----------|
| Pre-deployment | 1 day | 1 | Day 1 |
| Backend deployment | 2-3 hours | 0.5 | Day 2 (AM) |
| Frontend deployment | 1-2 hours | 0.5 | Day 2 (PM) |
| Stripe setup | 30 minutes | 0.25 | Day 2 (PM) |
| Testing | 4-6 hours | 1 | Day 3 |
| Monitoring setup | 1-2 hours | 0.5 | Day 3 (PM) |
| Production hardening | 2-3 hours | 0.5 | Day 4 |
| Launch & monitor | 1+ days | 1+ | Day 5+ |
| **Total** | - | **5-7 days** | - |

---

## Success Criteria

### Day 5 (Launch Ready)
- ✅ Backend deployed on Railway
- ✅ Frontend deployed on Vercel
- ✅ Database migrated and tested
- ✅ Stripe payments working
- ✅ Email sending verified
- ✅ All health checks passing
- ✅ Monitoring enabled
- ✅ Backups configured

### Week 1
- ✅ 0 critical errors
- ✅ 99% uptime
- ✅ <500ms API response
- ✅ 100% email delivery
- ✅ All payments processing

### Month 1
- ✅ Stable operations
- ✅ First users signed up
- ✅ Positive feedback
- ✅ Bug fixes deployed
- ✅ Monitoring refined

---

## Troubleshooting Quick Links

**Backend Issues**: See `MONITORING_GUIDE.md` → Debugging
**Database Issues**: See `MONITORING_GUIDE.md` → Database Troubleshooting
**Email Issues**: See `MONITORING_GUIDE.md` → Email Troubleshooting
**Payment Issues**: See `MONITORING_GUIDE.md` → Stripe Troubleshooting

---

## Support Contacts

- **Railway Support**: support@railway.app
- **Vercel Support**: support.vercel.com
- **Stripe Support**: support.stripe.com
- **GitHub Issues**: Open issue on repository

---

**Ready to deploy?** Start with Phase 1: Pre-Deployment.

**Next Step**: Follow `QUICK_START.md` for fast deployment, or `CREDENTIALS_SETUP.md` to gather all required credentials.

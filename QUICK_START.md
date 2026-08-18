# ⚡ PredictX Quick Start - 5 Minutes to Deployment

Deploy PredictX in 5 minutes using Railway and Vercel.

---

## Prerequisites (5 minutes setup)

### 1. Install Tools
```bash
# Install Railway CLI
npm install -g @railway/cli

# Install Vercel CLI
npm install -g vercel
```

### 2. Create Accounts (if needed)
- Railway: https://railway.app (sign up)
- Vercel: https://vercel.com (sign up)
- Stripe: https://stripe.com (sign up)
- Gmail: Enable 2FA for app passwords

### 3. Gather Credentials
Run from project directory:
```bash
# Generate JWT secret
openssl rand -base64 48
# Copy output

# Get Gmail app password
# Go to: https://accounts.google.com/account/security → App passwords
# Create Mail app password

# Get Stripe keys
# Go to: https://dashboard.stripe.com/apikeys
# Copy Secret Key
```

---

## Deploy Backend to Railway (2 minutes)

```bash
# Login to Railway
railway login
# Opens browser - click Authorize

# Initialize project
railway init
# Select "Create new project"

# Add PostgreSQL database
railway add postgres
# Auto-creates DATABASE_URL

# Add Redis (optional)
railway add redis

# Deploy backend
railway up
# Uploads code and builds

# Set environment variables
railway variable set REDIS_URL='redis://...'
railway variable set JWT_SECRET_KEY='your-secret'
railway variable set SMTP_SERVER='smtp.gmail.com'
railway variable set SMTP_PORT='587'
railway variable set SMTP_USER='your@gmail.com'
railway variable set SMTP_PASSWORD='your-app-password'
railway variable set STRIPE_API_KEY='sk_live_...'
railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'
railway variable set STRIPE_PRO_PRICE_ID='price_...'
railway variable set STRIPE_ENTERPRISE_PRICE_ID='price_...'
railway variable set FRONTEND_URL='https://your-frontend.com'
railway variable set ENVIRONMENT='production'
railway variable set DEBUG='false'

# Run migrations
railway run alembic upgrade head

# Get backend URL
railway domains
# Save output as your API URL
```

---

## Deploy Frontend to Vercel (1 minute)

```bash
# Login to Vercel
vercel login

# Deploy frontend
cd frontend
vercel --prod
# Opens browser to configure

# Set backend URL environment variable
vercel env add REACT_APP_API_URL
# Enter: https://your-railway-backend-url

# Redeploy with env vars
vercel --prod

# Get your frontend URL from Vercel dashboard
# Update Railway FRONTEND_URL variable
railway variable set FRONTEND_URL='https://your-vercel-url.com'
```

---

## Configure Stripe Webhooks (1 minute)

```bash
# Get your backend URL from Railway
railway domains
# Copy URL

# Go to Stripe: https://dashboard.stripe.com/webhooks
# Add new endpoint
# URL: https://your-backend-url/api/webhooks/stripe
# Events:
#   - customer.subscription.created
#   - customer.subscription.updated
#   - customer.subscription.deleted
#   - invoice.payment_succeeded
#   - invoice.payment_failed
#   - charge.refunded

# Copy webhook signing secret
# Set in Railway
railway variable set STRIPE_WEBHOOK_SECRET='whsec_...'
```

---

## Test It Works (1 minute)

### Backend Health
```bash
curl https://your-backend-url/health
# Should return: {"status":"ok"}
```

### API Docs
```bash
# Open in browser
https://your-backend-url/docs
```

### Frontend
```bash
# Open in browser
https://your-vercel-url.com
```

### Test Signup
1. Go to frontend URL
2. Click "Sign Up"
3. Enter email, username, password
4. Check email for verification link
5. Click link to verify
6. Dashboard should display

### Test Payment (Stripe Sandbox)
1. Go to Settings → Billing
2. Click "Upgrade to Pro"
3. Enter Stripe test card: 4242 4242 4242 4242
4. Any expiry date, any CVC
5. Should see "Subscription activated"

---

## Helpful Commands

### Check Status
```bash
railway status
railway logs -f
```

### Update Variables
```bash
railway variable set KEY=VALUE
railway variable list
railway variable delete KEY
```

### View Database
```bash
railway variable get DATABASE_URL
psql <your-database-url>
```

### Redeploy
```bash
railway up
```

### View Frontend
```bash
vercel --prod
```

---

## Common Issues

### Backend Not Deploying
```bash
# Check logs
railway logs

# Check environment variables
railway variable list

# Redeploy
railway up
```

### Email Not Sending
```bash
# Verify SMTP
railway logs | grep -i email

# Check credentials
railway variable list | grep SMTP
```

### Stripe Not Working
```bash
# Check webhook
# Go to Stripe → Webhooks → View logs

# Check API key
railway variable get STRIPE_API_KEY

# Check secret
railway variable get STRIPE_WEBHOOK_SECRET
```

### Database Error
```bash
# Check connection
railway run psql -c "SELECT 1"

# Run migrations
railway run alembic upgrade head
```

---

## Next Steps

✅ **1 hour to production** with Railway + Vercel

1. ✅ Backend deployed on Railway
2. ✅ Frontend deployed on Vercel
3. ✅ Database configured (PostgreSQL)
4. ✅ Payments setup (Stripe)
5. ✅ Email configured (Gmail)
6. ✅ Monitoring enabled (Railway logs)

### Additional Setup (Optional)
- [ ] Custom domain (buy domain, add CNAME)
- [ ] Email domain verification
- [ ] Monitoring (Sentry, UptimeRobot)
- [ ] Backups (Railway auto-backs up DB)

### Monitor Production
- Railway dashboard: https://railway.app
- Vercel dashboard: https://vercel.com
- Stripe dashboard: https://stripe.com
- Email logs: Check backend logs

---

## Support

- **Railway**: https://docs.railway.app
- **Vercel**: https://vercel.com/docs
- **Stripe**: https://stripe.com/docs
- **GitHub Issues**: Open an issue with logs

---

**You''re now live!** 🚀

PredictX is deployed and accepting users. Monitor logs and Stripe webhooks to ensure everything works.

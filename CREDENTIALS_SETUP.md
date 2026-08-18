# 🔑 PredictX Credentials Setup Guide

## Quick Setup (Non-Interactive)

```bash
# Set your credentials as environment variables
export DATABASE_URL='postgresql://user:pass@host:5432/predictx'
export REDIS_URL='redis://localhost:6379'
export JWT_SECRET_KEY='your-64-char-random-key'
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USER='your-email@gmail.com'
export SMTP_PASSWORD='your-16-char-app-password'
export STRIPE_API_KEY='sk_test_xxx'
export STRIPE_WEBHOOK_SECRET='whsec_xxx'
export STRIPE_PRO_PRICE_ID='price_xxx'
export STRIPE_ENTERPRISE_PRICE_ID='price_xxx'
export FRONTEND_URL='http://localhost:3000'

# Run automated setup
./setup-credentials-auto.sh
```

---

## Detailed Setup Instructions

### 1. Database URL

**Option A: Local PostgreSQL**
```
DATABASE_URL=postgresql://predictx:password@localhost:5432/predictx
```

**Option B: Railway**
1. Go to https://railway.app
2. Create project
3. Add PostgreSQL plugin
4. Copy connection string

**Option C: AWS RDS**
1. Create RDS instance
2. Get endpoint: `your-instance.c123.us-east-1.rds.amazonaws.com`
3. Format: `postgresql://admin:password@endpoint:5432/predictx`

### 2. Redis URL

**Option A: Local Redis**
```
REDIS_URL=redis://localhost:6379
```

**Option B: Redis Cloud**
1. Go to https://redis.com/try-free
2. Create database
3. Copy connection string

### 3. JWT Secret Key

Generate a secure 64-character key:
```bash
openssl rand -base64 48
```

Output will be something like:
```
jwt_secret_key_here_64_chars_long_random_string
```

Set:
```
export JWT_SECRET_KEY='jwt_secret_key_here_64_chars_long_random_string'
```

### 4. SMTP Configuration (Gmail)

**Step 1: Enable 2-Factor Authentication**
1. Go to https://myaccount.google.com
2. Security → 2-Step Verification → Enable

**Step 2: Generate App Password**
1. Security → App passwords
2. Select: Mail / Windows Computer
3. Google generates 16-character password
4. Copy it

**Step 3: Set Environment Variables**
```bash
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USER='your-email@gmail.com'
export SMTP_PASSWORD='xxxx xxxx xxxx xxxx'  # 16-char app password
```

### 5. Stripe API Keys

**Step 1: Create Stripe Account**
1. Go to https://stripe.com
2. Sign up / Login
3. Go to Dashboard

**Step 2: Get API Keys**
1. Developers → API keys
2. Copy Secret Key (sk_test_...)
3. Copy Webhook Secret (whsec_...)

**Step 3: Create Price IDs**
1. Products → New product
2. Create "Pro" plan: $29/month
3. Copy Price ID (price_...)
4. Create "Enterprise" plan: $0/month (custom)
5. Copy Price ID (price_...)

**Step 4: Set Environment Variables**
```bash
export STRIPE_API_KEY='sk_test_abc123...'
export STRIPE_WEBHOOK_SECRET='whsec_xyz789...'
export STRIPE_PRO_PRICE_ID='price_1234567890'
export STRIPE_ENTERPRISE_PRICE_ID='price_0987654321'
```

### 6. Frontend URL

For local development:
```bash
export FRONTEND_URL='http://localhost:3000'
```

For production:
```bash
export FRONTEND_URL='https://your-domain.com'
```

---

## Complete Setup Script

Copy and paste into your terminal:

```bash
#!/bin/bash

# 1. Generate JWT Secret
JWT_SECRET=$(openssl rand -base64 48)
echo "Generated JWT Secret: $JWT_SECRET"

# 2. Set all variables
export DATABASE_URL='postgresql://predictx:password@localhost:5432/predictx'
export REDIS_URL='redis://localhost:6379'
export JWT_SECRET_KEY="$JWT_SECRET"
export SMTP_SERVER='smtp.gmail.com'
export SMTP_PORT='587'
export SMTP_USER='your-email@gmail.com'
export SMTP_PASSWORD='xxxx xxxx xxxx xxxx'
export STRIPE_API_KEY='sk_test_...'
export STRIPE_WEBHOOK_SECRET='whsec_...'
export STRIPE_PRO_PRICE_ID='price_...'
export STRIPE_ENTERPRISE_PRICE_ID='price_...'
export FRONTEND_URL='http://localhost:3000'

# 3. Run setup
./setup-credentials-auto.sh
```

---

## Verification

After setup, verify your credentials:

```bash
# Check .env file
cat .env

# Test database
docker-compose exec postgres psql -U predictx -d predictx -c "SELECT 1"

# Test Redis
docker-compose exec redis redis-cli ping

# Test backend
curl http://localhost:8000/health
```

---

## Environment Variable Checklist

- [ ] `DATABASE_URL` - PostgreSQL connection
- [ ] `REDIS_URL` - Redis connection
- [ ] `JWT_SECRET_KEY` - 64-char random key (use openssl)
- [ ] `SMTP_SERVER` - smtp.gmail.com
- [ ] `SMTP_PORT` - 587
- [ ] `SMTP_USER` - your email
- [ ] `SMTP_PASSWORD` - 16-char Gmail app password
- [ ] `STRIPE_API_KEY` - sk_test_xxx
- [ ] `STRIPE_WEBHOOK_SECRET` - whsec_xxx
- [ ] `STRIPE_PRO_PRICE_ID` - price_xxx
- [ ] `STRIPE_ENTERPRISE_PRICE_ID` - price_xxx
- [ ] `FRONTEND_URL` - http://localhost:3000

---

## Troubleshooting

### "DATABASE_URL not set"
```bash
echo "Current DATABASE_URL: $DATABASE_URL"
# If empty, run: export DATABASE_URL='your-url'
```

### "SMTP Password rejected"
1. Verify you used Gmail App Password (not regular password)
2. Verify 2FA is enabled
3. Generate new app password if needed

### "Stripe key not working"
1. Verify you're using Secret Key (sk_live_ or sk_test_)
2. Check it's not the Publishable Key (pk_xxx)
3. Verify webhook secret is correct

---

## Next Steps

```bash
# 1. Setup credentials (run automated setup)
./setup-credentials-auto.sh

# 2. Deploy locally
./deploy.sh

# 3. Test everything
./test-deployment.sh

# 4. If tests pass, you're ready for production!
```


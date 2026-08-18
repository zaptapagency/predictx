# 🔐 PredictX Credentials Setup Guide

Complete guide for gathering and configuring all credentials needed for PredictX deployment.

**Time Required: 30-45 minutes**

---

## Table of Contents

1. [Database (PostgreSQL)](#database-postgresql)
2. [Redis](#redis)
3. [JWT Secret Key](#jwt-secret-key)
4. [SMTP (Email)](#smtp-email)
5. [Stripe (Payment)](#stripe-payment)
6. [Frontend Configuration](#frontend-configuration)
7. [Environment File Setup](#environment-file-setup)
8. [Verification Checklist](#verification-checklist)

---

## Database (PostgreSQL)

### Option 1: Railway (Recommended)

Railway automatically creates PostgreSQL database.

```bash
# During railway deployment
railway add postgres
railway variable get DATABASE_URL
```

**Output**: Connection string like `postgresql://user:password@host:port/dbname`

### Option 2: AWS RDS

1. Go to https://console.aws.amazon.com/rds
2. Click "Create Database"
3. Select PostgreSQL (latest version)
4. Choose "Free tier" if eligible
5. Set:
   - DB instance: predictx-prod
   - Username: postgres
   - Password: (strong password)
   - Public accessibility: Yes (or use VPN)

6. Wait 5-10 minutes for creation
7. Click instance → "Configuration" tab
8. Copy endpoint and port

**Connection String Format**:
```
postgresql://postgres:PASSWORD@endpoint:5432/postgres
```

### Option 3: DigitalOcean Managed Database

1. Go to https://cloud.digitalocean.com/databases
2. Click "Create Database"
3. Select PostgreSQL
4. Choose region same as droplet
5. Copy connection string

**Verification**:
```bash
psql "postgresql://user:password@host:port/dbname" -c "SELECT 1"
```

✅ If no error, connection works!

---

## Redis

### Option 1: Redis Cloud (Recommended - Free)

1. Go to https://app.redislabs.com
2. Sign up (free account)
3. Click "Create Database"
4. Choose:
   - Type: Redis
   - Size: Free (25 MB, no credit card)
   - Region: Closest to your backend
5. Wait for creation (< 1 minute)
6. Click database → "Configuration"
7. Copy "Redis URL" (looks like: `redis://default:password@host:port`)

**Save this** as your `REDIS_URL`

### Option 2: Railway Managed Redis

```bash
# During railway deployment
railway add redis
railway variable get REDIS_URL
```

### Option 3: Local Redis

```bash
# For local development only
docker run -d -p 6379:6379 redis:7
# REDIS_URL=redis://localhost:6379
```

**Verification**:
```bash
# Install redis-cli
brew install redis  # Mac
apt-get install redis-tools  # Linux

# Test connection
redis-cli -u "redis://user:password@host:port" ping
```

✅ Should return "PONG"

---

## JWT Secret Key

### Generate JWT Secret

```bash
# Generate 48-character random key
openssl rand -base64 48
```

**Output Example**:
```
VRY5TZ9w2K8mP7xQsN4hJLmKoI3pB6cD9eF2gH5jK8lM1nO4qR7sT0uV3wX6yZ9
```

**Copy and save** this as `JWT_SECRET_KEY`

**Security Note**: 
- Keep this secret
- Don''t commit to Git
- Different for each environment
- Must be at least 32 characters

---

## SMTP (Email)

### Option 1: Gmail with App Password (Recommended)

#### Step 1: Enable 2-Factor Authentication

1. Go to https://accounts.google.com/account/security
2. Click "2-Step Verification"
3. Follow prompts to enable

#### Step 2: Create App Password

1. Go to https://accounts.google.com/account/security
2. Click "App Passwords" (appears after 2FA enabled)
3. Select:
   - App: Mail
   - Device: Windows/Mac/Linux
4. Generate password
5. Copy the 16-character password

**Save as**:
- `SMTP_USER`: your-email@gmail.com
- `SMTP_PASSWORD`: 16-char app password from above
- `SMTP_SERVER`: smtp.gmail.com
- `SMTP_PORT`: 587

### Option 2: SendGrid

1. Go to https://sendgrid.com (free tier available)
2. Sign up
3. Go to Settings → API Keys
4. Create new API key
5. Click "Settings" → "Sender Authentication"
6. Add verified sender (your email)

**Save as**:
- `SMTP_USER`: apikey
- `SMTP_PASSWORD`: your-api-key
- `SMTP_SERVER`: smtp.sendgrid.net
- `SMTP_PORT`: 587

### Option 3: AWS SES

1. Go to https://console.aws.amazon.com/ses
2. Verify email address (confirm in inbox)
3. Go to Account Dashboard
4. Request production access
5. Create SMTP credentials

**Save as**:
- `SMTP_USER`: AWS access key ID
- `SMTP_PASSWORD`: AWS secret access key
- `SMTP_SERVER`: email-smtp.region.amazonaws.com
- `SMTP_PORT`: 587

### Option 4: Mailtrap (Development Only)

1. Go to https://mailtrap.io
2. Sign up (free tier)
3. Go to Demo Inbox → SMTP Settings
4. Copy credentials

**Save as**:
- `SMTP_USER`: username
- `SMTP_PASSWORD`: password
- `SMTP_SERVER`: smtp.mailtrap.io
- `SMTP_PORT`: 2525 or 465

**Verification**:
```bash
# Test SMTP connection (after deployment)
curl -X POST https://your-api.com/api/auth/password-reset \
  -H "Content-Type: application/json" \
  -d ''"'"'{"email": "test@example.com"}'"'"''

# Check email inbox for reset link
```

---

## Stripe (Payment)

### Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Click "Start now"
3. Enter email and password
4. Complete onboarding

### Step 2: Get API Keys

1. Go to https://dashboard.stripe.com/apikeys
2. Copy:
   - **Publishable Key**: pk_live_...
   - **Secret Key**: sk_live_...

**Save as**:
- `STRIPE_API_KEY`: sk_live_...

### Step 3: Create Subscription Plans

1. Go to https://dashboard.stripe.com/products
2. Click "Create product"

**Create 3 Products**:

**Product 1: Pro Plan**
- Name: PredictX Pro
- Description: 10,000 predictions/month
- Price: $29/month
- Recurring: Monthly
- Copy Price ID (price_...)

**Product 2: Enterprise Plan**
- Name: PredictX Enterprise  
- Description: Unlimited predictions
- Price: $299/month
- Recurring: Monthly
- Copy Price ID (price_...)

**Product 3: Free Plan** (optional)
- Name: PredictX Free
- Description: 100 predictions/month
- Free (no price needed)

**Save as**:
- `STRIPE_PRO_PRICE_ID`: price_... (from Pro product)
- `STRIPE_ENTERPRISE_PRICE_ID`: price_... (from Enterprise product)

### Step 4: Setup Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Set URL: `https://your-api.com/api/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `charge.refunded`
5. Click "Add endpoint"
6. Click endpoint → "Signing secret"
7. Copy signing secret

**Save as**:
- `STRIPE_WEBHOOK_SECRET`: whsec_...

### Testing Stripe in Development

**Test Card Numbers**:
- Visa: 4242 4242 4242 4242
- Mastercard: 5555 5555 5555 4444
- Amex: 3782 822463 10005

**Expiry**: Any future date  
**CVC**: Any 3 digits

---

## Frontend Configuration

### Get Backend URL

After deploying backend to Railway:
```bash
railway domains
```

**Output**:
```
predictx-backend-production.railway.app
```

**Save as**:
- `REACT_APP_API_URL`: https://predictx-backend-production.railway.app
- `FRONTEND_URL`: https://your-frontend-domain.com (for backend email links)

### Frontend Environment Variables

Create `.env.local` in `frontend/` directory:

```env
REACT_APP_API_URL=https://your-backend-url.com
```

---

## Environment File Setup

### Create .env for Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://default:password@host:port

# JWT
JWT_SECRET_KEY=your-64-char-secret-from-openssl

# SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password

# Stripe
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# Frontend
FRONTEND_URL=https://your-frontend.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Create .env for Frontend

```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local`:

```env
REACT_APP_API_URL=https://your-backend.com
```

---

## Verification Checklist

### Database
- [ ] PostgreSQL created and accessible
- [ ] Database URL copied
- [ ] Can connect: `psql "postgresql://..."`
- [ ] Migration runs without error

### Redis
- [ ] Redis created (Cloud or local)
- [ ] Connection string copied
- [ ] Can connect: `redis-cli -u "redis://..."`

### JWT
- [ ] Secret key generated (48+ characters)
- [ ] Saved securely

### SMTP
- [ ] Email/password configured
- [ ] Test email sends successfully
- [ ] Verification emails working

### Stripe
- [ ] API key copied (sk_live_...)
- [ ] Webhook secret copied (whsec_...)
- [ ] Pro price ID copied (price_...)
- [ ] Enterprise price ID copied (price_...)
- [ ] Webhook endpoint added

### Frontend
- [ ] Backend URL known
- [ ] Frontend domain configured
- [ ] Environment variables set

### Final Check
```bash
# All variables set
grep -v ''^#'' .env | grep -v ''^$''

# Should show 13 variables with values
```

---

## Security Best Practices

### DO
- [ ] Use different secrets for dev/prod
- [ ] Store secrets in environment variables, not code
- [ ] Never commit .env files to Git
- [ ] Regenerate JWT secret annually
- [ ] Rotate API keys quarterly
- [ ] Use webhook signatures for verification

### DON''T
- [ ] Don''t share secrets in chat/email
- [ ] Don''t commit .env to version control
- [ ] Don''t use simple/common secrets
- [ ] Don''t use same secret across environments
- [ ] Don''t expose secrets in logs
- [ ] Don''t hardcode credentials in code

---

## Troubleshooting

### Database Connection Failed
```bash
# Check URL format
echo $DATABASE_URL

# Test with psql
psql $DATABASE_URL -c "SELECT 1"

# Check firewall/security groups
```

### Email Not Sending
```bash
# Verify SMTP settings
grep SMTP .env

# Check app password in Gmail
# Ensure 2FA enabled
# Try test email after deployment
```

### Stripe Webhook Not Working
```bash
# Check webhook secret
grep STRIPE_WEBHOOK .env

# Monitor in Stripe dashboard
# Check API error logs
```

### Redis Connection Failed
```bash
# Check URL format
echo $REDIS_URL

# Test connection
redis-cli -u $REDIS_URL ping

# Should return PONG
```

---

## Next Steps

1. Gather all credentials (this guide)
2. Create .env files
3. Deploy to Railway: `./deploy-railway.sh`
4. Run migrations: `railway run alembic upgrade head`
5. Deploy frontend to Vercel
6. Configure Stripe webhook
7. Test end-to-end flows
8. Monitor in production

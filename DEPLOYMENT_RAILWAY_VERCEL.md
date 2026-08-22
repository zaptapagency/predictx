# Deploy ForecastX on Railway + Vercel

Complete production deployment guide for backend (Railway) + frontend (Vercel).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VERCEL (Frontend)                       │
│  - Next.js/React app                                        │
│  - Auto-deploys from GitHub                                 │
│  - Global CDN                                               │
│  - Environment variables via Vercel dashboard               │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY (Backend)                        │
│  - FastAPI Python app                                       │
│  - PostgreSQL database                                      │
│  - Redis cache (optional)                                   │
│  - Auto-deploys from GitHub                                │
│  - Logs + monitoring built-in                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Create Accounts (if needed)
- Railway: https://railway.app (free tier available)
- Vercel: https://vercel.com (free tier available)
- GitHub: https://github.com (free tier)

### Get Credentials Ready
1. **Salesforce OAuth** (from Salesforce App Manager)
   - Client ID
   - Client Secret
   - Redirect URI: `https://your-api-domain.com/auth/salesforce/callback`

2. **Database** (Railway handles this)
   - PostgreSQL instance (auto-created by Railway)

3. **Email Service** (choose one)
   - SendGrid API key, OR
   - Mailgun API key, OR
   - AWS SES credentials

---

## Step 1: Prepare GitHub Repository

### 1a. Push code to GitHub
```bash
cd ~/Desktop/forecastx
git remote add origin https://github.com/your-username/forecastx.git
git branch -M main
git push -u origin main
```

### 1b. Directory structure (verify)
```
forecastx/
├── backend/                    # FastAPI app
│   ├── app/
│   │   ├── main.py            # Entry point
│   │   ├── api/
│   │   ├── db/
│   │   ├── services/
│   │   └── models/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile             # (we'll create)
│
├── frontend/                   # React/Next.js app
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
│
└── docker-compose.yml
```

### 1c. Create backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1d. Create backend .env.example
```env
# backend/.env.example
DATABASE_URL=postgresql://user:password@localhost:5432/forecastx
SQLALCHEMY_DATABASE_URL=postgresql://user:password@localhost:5432/forecastx

# Salesforce OAuth
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REDIRECT_URI=https://your-api-domain.com/auth/salesforce/callback

# Email Service
SENDGRID_API_KEY=your_sendgrid_key
SENDGRID_FROM_EMAIL=noreply@forecastx.com

# JWT
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
FRONTEND_URL=https://your-frontend-domain.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

### 1e. Create frontend .env.example
```env
# frontend/.env.example
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_SALESFORCE_CLIENT_ID=your_client_id
REACT_APP_ENV=production
```

### 1f. Commit and push
```bash
git add .
git commit -m "Prepare for Railway + Vercel deployment"
git push origin main
```

---

## Step 2: Deploy Backend on Railway

### 2a. Create Railway Project
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect GitHub (authorize Railway)
5. Select `forecastx` repository
6. Select `backend` directory as root

### 2b. Add PostgreSQL Service
1. In Railway dashboard, click "Add service"
2. Select "PostgreSQL"
3. Railway auto-creates database
4. Note connection string (Railway shows it)

### 2c. Configure Environment Variables
In Railway dashboard → forecastx project → Variables:

```
DATABASE_URL=postgresql://postgres:PASSWORD@postgres-service:5432/forecastx
SQLALCHEMY_DATABASE_URL=postgresql://postgres:PASSWORD@postgres-service:5432/forecastx

SALESFORCE_CLIENT_ID=your_salesforce_client_id
SALESFORCE_CLIENT_SECRET=your_salesforce_client_secret
SALESFORCE_REDIRECT_URI=https://your-railway-domain.com/auth/salesforce/callback

SENDGRID_API_KEY=your_sendgrid_key
SENDGRID_FROM_EMAIL=noreply@forecastx.com

SECRET_KEY=generate-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

FRONTEND_URL=https://your-vercel-domain.com

ENVIRONMENT=production
DEBUG=false
```

### 2d. Deploy
1. Railway auto-deploys on git push
2. Check deployment logs in Railway dashboard
3. Once deployed, note your API URL: `https://your-railway-domain.com`

### 2e. Run Database Migrations
In Railway → Deployments → Click latest → View logs:

```bash
# SSH into Railway container
railway up

# Or via CLI
railway run alembic upgrade head
```

---

## Step 3: Deploy Frontend on Vercel

### 3a. Import Project
1. Go to https://vercel.com/new
2. Select "Import Git Repository"
3. Paste your GitHub repo URL: `https://github.com/your-username/forecastx`
4. Vercel detects it's monorepo
5. Set root directory: `frontend`
6. Continue

### 3b. Configure Environment Variables
In Vercel dashboard → Settings → Environment Variables:

```
REACT_APP_API_BASE_URL=https://your-railway-domain.com
REACT_APP_SALESFORCE_CLIENT_ID=your_salesforce_client_id
REACT_APP_ENV=production
```

### 3c. Deploy
1. Click "Deploy"
2. Vercel builds and deploys
3. Once done, you get URL: `https://your-vercel-domain.com`

---

## Step 4: Update Salesforce OAuth

Now that you have both URLs, update Salesforce:

### In Salesforce App Manager:
1. Open your Connected App
2. Update Redirect URI: `https://your-railway-domain.com/auth/salesforce/callback`
3. Update allowed origins: `https://your-vercel-domain.com`
4. Save

### Update Environment Variables:
- Railway: `SALESFORCE_REDIRECT_URI=https://your-railway-domain.com/auth/salesforce/callback`
- Vercel: `REACT_APP_API_BASE_URL=https://your-railway-domain.com`
- Redeploy both

---

## Step 5: Custom Domain (Optional)

### Connect Domain to Vercel
1. Vercel dashboard → Settings → Domains
2. Add custom domain
3. Follow DNS setup (Vercel shows steps)
4. Wait 5-10 min for DNS propagation

### Connect Domain to Railway (API)
1. Railway dashboard → Settings → Domains
2. Add custom domain for API
3. Update DNS records
4. Update `SALESFORCE_REDIRECT_URI` with new domain

---

## Step 6: Health Checks

### Verify Backend is Running
```bash
curl https://your-railway-domain.com/health
# Should return: {"status": "ok"}
```

### Verify Database Connection
```bash
# Via Railway dashboard → Deployments → Logs
# Should show: Database connection successful
```

### Verify Frontend is Running
Open browser: `https://your-vercel-domain.com`
Should load ForecastX homepage

### Test Onboarding Flow
1. Sign up for new account
2. Go through onboarding
3. Verify each step saves to database
4. Check logs for errors

---

## Step 7: Set Up Monitoring

### Railway Monitoring
- Built-in: CPU, memory, disk usage
- Dashboard auto-shows: Deployments, logs, metrics
- Alerts: Set via Railway dashboard

### Vercel Monitoring
- Built-in: Performance metrics, error tracking
- Analytics dashboard: Shows page load times
- Alerts: Via email on deployment failures

### Add Error Tracking (Optional)
Use Sentry for error monitoring:

```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production"
)
```

---

## Step 8: Verify Everything Works

### Checklist
- [ ] Backend API responding
- [ ] Frontend loads
- [ ] Database connected
- [ ] Onboarding flow works end-to-end
- [ ] Salesforce OAuth works
- [ ] Emails send (if configured)
- [ ] Logs visible in dashboards
- [ ] Monitoring/alerts working

---

## Troubleshooting

### Issue: "Cannot connect to database"
**Solution**: 
1. Verify `DATABASE_URL` in Railway
2. Check PostgreSQL service is running
3. Ensure connection string format: `postgresql://user:pass@host:5432/db`

### Issue: "Salesforce OAuth redirect mismatch"
**Solution**:
1. Check `SALESFORCE_REDIRECT_URI` in Railway env vars
2. Verify it matches exactly in Salesforce app
3. Check for trailing slashes or protocol differences

### Issue: "CORS error from frontend"
**Solution**:
1. Verify `FRONTEND_URL` in Railway
2. Check CORS headers in FastAPI app
3. Ensure protocol matches (https, not http)

### Issue: "500 error on onboarding"
**Solution**:
1. Check Railway logs: `railway logs`
2. Look for database/migration errors
3. Verify all required tables exist
4. Run migrations: `railway run alembic upgrade head`

### Issue: "Frontend env vars not loading"
**Solution**:
1. Verify vars start with `REACT_APP_`
2. Redeploy Vercel (changes require rebuild)
3. Check `.env` file in frontend root (not committed)
4. Clear browser cache

---

## Post-Launch Monitoring (24 Hours)

### Hour 1
- [ ] Check error logs for crashes
- [ ] Monitor CPU/memory usage
- [ ] Verify no database connection issues

### Hour 6
- [ ] Check onboarding completion rate
- [ ] Verify Salesforce connections working
- [ ] Monitor API response times

### Hour 24
- [ ] Analyze performance metrics
- [ ] Check user feedback/support tickets
- [ ] Review error trends
- [ ] Plan fixes for day 2

---

## Rollback Plan

If something breaks in production:

### Quick Rollback (5 min)
```bash
# Railway: Revert to previous deployment
# Dashboard → Deployments → Click previous → "Redeploy"

# Vercel: Revert to previous deployment
# Dashboard → Deployments → Click previous → "Redeploy"
```

### Full Rollback (15 min)
```bash
# Git: Revert last commit
git revert HEAD
git push origin main

# Both Railway and Vercel auto-redeploy from git
# Takes 3-5 min to build and deploy
```

---

## Cost Estimate (Monthly)

| Service | Cost | Notes |
|---------|------|-------|
| Railway Backend | $7-50 | Starter plan includes credit |
| Railway Database | Free | $5+ if scaling needed |
| Vercel Frontend | Free | Unlimited deployments |
| Salesforce | Varies | Your existing plan |
| SendGrid Email | Free | Up to 100 emails/day free |
| **Total** | **~$12/mo** | Very affordable for MVP |

---

## Next Steps After Launch

1. **Day 2**: Iterate on feedback
2. **Week 1**: Monitor metrics, improve onboarding
3. **Week 2**: Add custom domain
4. **Week 3**: Scale infrastructure if needed
5. **Month 1**: Add monitoring/analytics

---

## Support

**Questions?** Check:
1. Railway docs: https://docs.railway.app
2. Vercel docs: https://vercel.com/docs
3. FastAPI docs: https://fastapi.tiangolo.com
4. React docs: https://react.dev

**Still stuck?** Open issues on GitHub with logs/screenshots.

---

## Success Criteria

✅ Backend API responding to requests
✅ Frontend loads in browser
✅ Database migrations completed
✅ Onboarding flow works end-to-end
✅ Salesforce OAuth completes
✅ No errors in logs
✅ Monitoring dashboards showing metrics
✅ Users can sign up and see predictions

**Timeline**: 1-2 hours from start to live deployment.

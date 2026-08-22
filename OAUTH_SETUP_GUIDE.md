# 🔐 OAUTH SETUP GUIDE - Zero Friction Signup

Complete guide to set up Google & Microsoft OAuth for instant user signup.

---

## 🎯 OVERVIEW

**What you're building:**
```
User clicks "Sign in with Google"
  ↓ (20 seconds)
Auto-detect company from email
  ↓
Create account instantly (no password!)
  ↓ (1 second)
See sample prediction dashboard
  ↓
User is now activated
```

**Result:** User to first value in <60 seconds

---

## 📋 PREREQUISITES

- Frontend: React + @react-oauth/google library
- Backend: FastAPI + Google OAuth2 library
- OAuth clients registered with Google & Microsoft

---

## ⚙️ PART 1: GOOGLE OAUTH SETUP

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (name: "ForecastX")
3. Enable APIs:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" → Enable
   - Search for "Google Identity Services" → Enable

### Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose: "Web application"
4. Name: "ForecastX Web"
5. **Authorized JavaScript origins:**
   ```
   http://localhost:3000
   https://build-210v6x5z0-boomboomlegacy25-4771s-projects.vercel.app (your Vercel URL)
   ```
6. **Authorized redirect URIs:**
   ```
   http://localhost:3000
   http://localhost:3000/auth/callback
   https://yourdomain.com
   https://yourdomain.com/auth/callback
   ```
7. Copy: **Client ID** and **Client Secret**

### Step 3: Add to Environment Variables

**Frontend (.env):**
```bash
REACT_APP_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
```

**Backend (.env):**
```bash
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
```

### Step 4: Install Frontend Library

```bash
cd frontend
npm install @react-oauth/google
```

### Step 5: Wrap App with GoogleOAuthProvider

**frontend/src/main.tsx or index.tsx:**
```typescript
import { GoogleOAuthProvider } from '@react-oauth/google'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID!}>
      <App />
    </GoogleOAuthProvider>
  </React.StrictMode>,
)
```

---

## ⚙️ PART 2: MICROSOFT OAUTH SETUP

### Step 1: Register Application

1. Go to [Azure AD Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Click "New registration"
3. Name: "ForecastX"
4. Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
5. Redirect URI: "Web" → `http://localhost:3000/auth/callback/microsoft`

### Step 2: Get Credentials

1. Go to "Certificates & secrets"
2. New client secret
3. Copy: **Client ID** and **Client Secret** value

### Step 3: Add API Permissions

1. Go to "API permissions"
2. Add permission → Microsoft Graph
3. Select: `openid`, `profile`, `email`
4. Grant admin consent

### Step 4: Add to Environment Variables

**Frontend (.env):**
```bash
REACT_APP_MICROSOFT_CLIENT_ID=YOUR_CLIENT_ID_HERE
```

**Backend (.env):**
```bash
MICROSOFT_CLIENT_ID=YOUR_CLIENT_ID_HERE
MICROSOFT_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
```

---

## 🔧 PART 3: BACKEND SETUP

### Step 1: Install Dependencies

```bash
cd backend
pip install google-auth google-auth-oauthlib google-auth-httplib2
pip install python-multipart  # For form data
```

### Step 2: Update Config

**backend/app/config.py:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    
    # URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

settings = Settings()
```

### Step 3: Register OAuth Routes

**backend/app/main.py:**
```python
from app.api import oauth

app.include_router(oauth.router)
```

### Step 4: Update Models

Make sure User model has these fields:

```python
# backend/app/db/models_saas.py

class User(Base):
    # ... existing fields ...
    picture_url: str = None  # For Google/Microsoft profile pic
    email_verified: bool = False  # Auto-verified via OAuth
```

Run migration:
```bash
alembic revision --autogenerate -m "Add picture_url and email_verified to User"
alembic upgrade head
```

---

## 🎨 PART 4: FRONTEND SETUP

### Step 1: Create SignupOAuth Component

✅ Already created: `frontend/src/pages/SignupOAuth.tsx`

### Step 2: Create Onboarding Page

✅ Already created: `frontend/src/pages/OnboardingSamplePrediction.tsx`

### Step 3: Add Styling

✅ Already created: `frontend/src/styles/onboarding.css`

### Step 4: Update App Routes

✅ Already updated: `frontend/src/App.tsx`

---

## 🚀 PART 5: DEPLOYMENT

### Frontend (Vercel)

1. Push to GitHub
2. Connect to Vercel
3. Set environment variable:
   ```
   REACT_APP_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
   REACT_APP_MICROSOFT_CLIENT_ID=YOUR_CLIENT_ID
   ```
4. Redeploy

### Backend (Railway)

1. Set environment variables in Railway dashboard:
   ```
   GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
   MICROSOFT_CLIENT_ID=YOUR_CLIENT_ID
   MICROSOFT_CLIENT_SECRET=YOUR_SECRET
   FRONTEND_URL=https://yourdomain.com
   ```
2. Redeploy

### Update OAuth Redirect URIs

**Google Console:**
- Add: `https://yourdomain.com`
- Add: `https://yourdomain.com/auth/callback`

**Azure Portal:**
- Add redirect URI: `https://yourdomain.com/auth/callback/microsoft`

---

## 🧪 TESTING LOCALLY

### Start Frontend
```bash
cd frontend
REACT_APP_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID npm start
```

### Start Backend
```bash
cd backend
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID python -m uvicorn app.main:app --reload
```

### Test OAuth Flow

1. Open http://localhost:3000
2. Click "Sign up"
3. Click "Sign in with Google"
4. Complete Google login
5. Should redirect to `/onboarding/sample-prediction`
6. See sample churn predictions

---

## ✅ CHECKLIST

### Google OAuth
- [ ] Google Cloud Project created
- [ ] OAuth 2.0 credentials created
- [ ] Client ID copied to .env files
- [ ] Redirect URIs configured in Google Console
- [ ] @react-oauth/google installed
- [ ] GoogleOAuthProvider wraps app
- [ ] SignupOAuth component using Google login

### Microsoft OAuth
- [ ] Azure AD app registered
- [ ] Client ID & Secret copied to .env files
- [ ] Redirect URIs configured in Azure
- [ ] API permissions set
- [ ] Backend handles Microsoft callback

### Deployment
- [ ] Environment variables set in Vercel
- [ ] Environment variables set in Railway
- [ ] OAuth redirect URIs updated for production
- [ ] Tested login flow end-to-end

---

## 🐛 TROUBLESHOOTING

### Error: "Google OAuth credentials not found"
**Fix:** Check REACT_APP_GOOGLE_CLIENT_ID in frontend/.env

### Error: "Invalid redirect URI"
**Fix:** Add all frontend URLs to Google/Azure console

### Error: "Token verification failed"
**Fix:** Ensure GOOGLE_CLIENT_ID matches frontend client ID

### Error: "CORS error"
**Fix:** Backend needs to allow frontend origin:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### User created but no organization
**Fix:** Check extract_email_domain() function in oauth.py

---

## 📊 VERIFY SETUP

Test endpoint (curl):
```bash
# Test Google token (get token from frontend console)
curl -X POST http://localhost:8000/api/auth/oauth/google \
  -H "Content-Type: application/json" \
  -d '{"credential": "YOUR_GOOGLE_TOKEN"}'
```

Expected response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@acme.com",
    "name": "John Doe"
  },
  "organization": {
    "id": 1,
    "name": "Acme",
    "domain": "acme.com"
  },
  "redirect_to": "/onboarding/sample-prediction"
}
```

---

## 🎯 WHAT'S NEXT

After OAuth is working:

1. ✅ User signs up instantly
2. ✅ Sees sample prediction
3. ❌ Needs to connect real data (Salesforce/Stripe)
4. ❌ Needs retention email sequences
5. ❌ Needs team invitations

---

## 📞 SUPPORT

If OAuth isn't working:

1. Check browser console for errors
2. Check backend logs: `docker logs forecastx-backend`
3. Verify tokens at [JWT.io](https://jwt.io)
4. Verify CORS settings
5. Verify environment variables are loaded

---

**Status: READY TO IMPLEMENT**

All code is written. Run through this setup guide to get OAuth working in 30 minutes.

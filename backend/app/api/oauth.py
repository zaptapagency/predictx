"""
OAuth2 authentication endpoints (Google, Microsoft)
Zero-friction signup: OAuth → Auto-detect company → Create user → Redirect to dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import jwt
import os
from google.auth.transport import requests
from google.oauth2 import id_token

from app.db.models_saas import User, Organization
from app.services.auth_service import create_access_token, hash_password
from app.config import settings
from app.db.database import get_db
from app.utils.time import utcnow

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============================================================================
# OAUTH HELPER FUNCTIONS
# ============================================================================

def extract_email_domain(email: str) -> str:
    """Extract domain from email (acme.com from user@acme.com)"""
    return email.split('@')[1].lower()

def detect_company_name(domain: str) -> str:
    """Guess company name from email domain"""
    # Remove common TLDs and subdomains
    parts = domain.replace('.com', '').replace('.io', '').replace('.co', '').split('.')
    company_name = parts[-1].capitalize()  # Last part (most specific)
    return company_name

def find_or_create_organization(db: Session, domain: str, email: str) -> Organization:
    """Find existing org by domain, or create new one"""

    # Check if org already exists
    existing_org = db.query(Organization).filter(
        Organization.domain == domain
    ).first()

    if existing_org:
        return existing_org

    # Create new organization
    company_name = detect_company_name(domain)
    new_org = Organization(
        name=company_name,
        domain=domain,
        created_at=utcnow(),
    )
    db.add(new_org)
    db.flush()  # Get the ID without committing

    return new_org

# ============================================================================
# GOOGLE OAUTH ENDPOINT
# ============================================================================

@router.post("/oauth/google")
def google_oauth(
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Google OAuth signup/login

    Flow:
    1. Frontend sends Google ID token
    2. Verify token with Google's public key
    3. Extract email + name
    4. Auto-detect company from email domain
    5. Find or create organization
    6. Find or create user
    7. Return JWT + user + org
    8. Frontend redirects to /onboarding/sample-prediction

    Timeline: <1 second
    """

    try:
        # ====================================================================
        # STEP 1: Verify Google token
        # ====================================================================
        credential = payload.get('credential')
        if not credential:
            raise HTTPException(
                status_code=400,
                detail="No credential provided"
            )

        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise HTTPException(
                status_code=503,
                detail="Google sign-in is not configured. Set GOOGLE_OAUTH_CLIENT_ID.",
            )

        try:
            # Verify token with Google's public key (cached by requests library)
            idinfo = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )

            # Verify token wasn't used for a different app
            if idinfo['aud'] != settings.GOOGLE_OAUTH_CLIENT_ID:
                raise ValueError('Token audience mismatch')

        except ValueError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )

        # ====================================================================
        # STEP 2: Extract user info from token
        # ====================================================================
        email = idinfo.get('email')
        name = idinfo.get('name', email)
        picture = idinfo.get('picture')

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not found in token"
            )

        # ====================================================================
        # STEP 3: Auto-detect company from email domain
        # ====================================================================
        domain = extract_email_domain(email)

        # ====================================================================
        # STEP 4: Find or create organization
        # ====================================================================
        organization = find_or_create_organization(db, domain, email)

        # ====================================================================
        # STEP 5: Find or create user
        # ====================================================================
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # New user - create account
            user = User(
                email=email,
                name=name,
                organization_id=organization.id,
                picture_url=picture,
                email_verified=True,  # Email verified by Google
                is_active=True,
                created_at=utcnow(),
            )
            db.add(user)
        else:
            # Existing user - update last login
            user.last_login = utcnow()

            # If user is in different org, link them
            if not user.organization_id:
                user.organization_id = organization.id

        db.commit()

        # ====================================================================
        # STEP 6: Generate JWT token
        # ====================================================================
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        # ====================================================================
        # STEP 7: Return response
        # ====================================================================
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture_url": user.picture_url,
                "organization_id": organization.id,
            },
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "domain": organization.domain,
            },
            "redirect_to": "/onboarding/sample-prediction"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth processing failed: {str(e)}"
        )


# ============================================================================
# MICROSOFT OAUTH ENDPOINT (Callback)
# ============================================================================

@router.get("/oauth/microsoft/callback")
def microsoft_oauth_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    Microsoft OAuth callback

    User is redirected here after signing in with Microsoft
    """

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code")

    try:
        # Exchange code for token (in production, do this server-to-server)
        # This is simplified - in production use msal library

        if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Microsoft sign-in is not configured. "
                    "Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET."
                ),
            )

        import requests as http_requests

        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

        data = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "code": code,
            "redirect_uri": f"{settings.FRONTEND_URL}/auth/callback/microsoft",
            "grant_type": "authorization_code",
            "scope": "openid profile email"
        }

        response = http_requests.post(token_url, data=data)
        token_data = response.json()

        if 'error' in token_data:
            raise HTTPException(
                status_code=401,
                detail=token_data.get('error_description', 'Token exchange failed')
            )

        # Get user info from Microsoft Graph API
        access_token = token_data['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = http_requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to get user info")

        user_info = user_response.json()
        email = user_info.get('userPrincipalName') or user_info.get('mail')
        name = user_info.get('displayName', email)

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Microsoft account")

        # ====================================================================
        # Auto-detect company and create/find user (same as Google)
        # ====================================================================
        domain = extract_email_domain(email)
        organization = find_or_create_organization(db, domain, email)

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                name=name,
                organization_id=organization.id,
                email_verified=True,
                is_active=True,
                created_at=utcnow(),
            )
            db.add(user)
        else:
            user.last_login = utcnow()
            if not user.organization_id:
                user.organization_id = organization.id

        db.commit()

        # Generate JWT and redirect
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        # Return redirect response (frontend will handle)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "redirect_to": "/onboarding/sample-prediction"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Microsoft OAuth failed: {str(e)}"
        )


# ============================================================================
# VERIFY TOKEN ENDPOINT (For frontend to check if user is logged in)
# ============================================================================

@router.get("/verify")
def verify_token(token: str = None, db: Session = Depends(get_db)):
    """Verify if token is valid"""

    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return {
            "valid": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            }
        }

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

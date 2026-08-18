#!/bin/bash

# PredictX Railway Deployment Script
# Automates complete deployment to Railway

set -e

echo "🚀 PredictX Railway Deployment"
echo "=============================="
echo ""

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠ Railway CLI not found${NC}"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 1: Railway Login
echo -e "${BLUE}Step 1: Authenticating with Railway${NC}"
railway login

echo ""

# Step 2: Initialize Project
echo -e "${BLUE}Step 2: Initializing Railway project${NC}"
railway init

echo ""

# Step 3: Add PostgreSQL
echo -e "${BLUE}Step 3: Adding PostgreSQL database${NC}"
echo "Setting up PostgreSQL plugin..."
railway add postgres

echo ""

# Step 4: Set Environment Variables
echo -e "${BLUE}Step 4: Configuring environment variables${NC}"
echo ""
echo "You'll need to set these environment variables in Railway:"
echo "  1. DATABASE_URL (auto-configured from PostgreSQL)"
echo "  2. REDIS_URL (get from Redis Cloud or configure manually)"
echo "  3. JWT_SECRET_KEY"
echo "  4. SMTP_* (email configuration)"
echo "  5. STRIPE_* (Stripe keys)"
echo "  6. FRONTEND_URL"
echo ""

read -p "Continue to set environment variables? (y/n): " continue_setup

if [ "$continue_setup" != "y" ]; then
    echo "Skipping environment setup. Run 'railway variable set KEY=value' manually."
    exit 0
fi

echo ""
echo -e "${YELLOW}Enter your environment variables (or leave blank to skip):${NC}"
echo ""

read -p "REDIS_URL: " REDIS_URL
[ ! -z "$REDIS_URL" ] && railway variable set REDIS_URL="$REDIS_URL"

read -p "JWT_SECRET_KEY (run: openssl rand -base64 48): " JWT_SECRET_KEY
[ ! -z "$JWT_SECRET_KEY" ] && railway variable set JWT_SECRET_KEY="$JWT_SECRET_KEY"

read -p "SMTP_SERVER (smtp.gmail.com): " SMTP_SERVER
[ ! -z "$SMTP_SERVER" ] && railway variable set SMTP_SERVER="$SMTP_SERVER"

read -p "SMTP_PORT (587): " SMTP_PORT
[ ! -z "$SMTP_PORT" ] && railway variable set SMTP_PORT="$SMTP_PORT"

read -p "SMTP_USER (your-email@gmail.com): " SMTP_USER
[ ! -z "$SMTP_USER" ] && railway variable set SMTP_USER="$SMTP_USER"

read -sp "SMTP_PASSWORD (16-char app password): " SMTP_PASSWORD
echo ""
[ ! -z "$SMTP_PASSWORD" ] && railway variable set SMTP_PASSWORD="$SMTP_PASSWORD"

read -sp "STRIPE_API_KEY (sk_live_...): " STRIPE_API_KEY
echo ""
[ ! -z "$STRIPE_API_KEY" ] && railway variable set STRIPE_API_KEY="$STRIPE_API_KEY"

read -sp "STRIPE_WEBHOOK_SECRET (whsec_...): " STRIPE_WEBHOOK_SECRET
echo ""
[ ! -z "$STRIPE_WEBHOOK_SECRET" ] && railway variable set STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET"

read -p "STRIPE_PRO_PRICE_ID: " STRIPE_PRO_PRICE_ID
[ ! -z "$STRIPE_PRO_PRICE_ID" ] && railway variable set STRIPE_PRO_PRICE_ID="$STRIPE_PRO_PRICE_ID"

read -p "STRIPE_ENTERPRISE_PRICE_ID: " STRIPE_ENTERPRISE_PRICE_ID
[ ! -z "$STRIPE_ENTERPRISE_PRICE_ID" ] && railway variable set STRIPE_ENTERPRISE_PRICE_ID="$STRIPE_ENTERPRISE_PRICE_ID"

read -p "FRONTEND_URL (https://your-domain.com): " FRONTEND_URL
[ ! -z "$FRONTEND_URL" ] && railway variable set FRONTEND_URL="$FRONTEND_URL"

echo ""

# Step 5: Deploy Backend
echo -e "${BLUE}Step 5: Deploying backend to Railway${NC}"
railway up

echo ""

# Step 6: Get Backend URL
echo -e "${BLUE}Step 6: Getting your backend URL${NC}"
BACKEND_URL=$(railway domains)

echo -e "${GREEN}✓ Backend URL: $BACKEND_URL${NC}"
echo ""

# Step 7: Database Migrations
echo -e "${BLUE}Step 7: Running database migrations${NC}"
echo "Running: railway run alembic upgrade head"
railway run alembic upgrade head

echo ""

# Step 8: Verify Deployment
echo -e "${BLUE}Step 8: Verifying deployment${NC}"
echo "Checking health endpoint..."

sleep 5

if curl -s "$BACKEND_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed - backend may still be starting${NC}"
fi

echo ""

# Step 9: Next Steps
echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Deploy Frontend (Vercel):"
echo "   npm i -g vercel"
echo "   cd frontend"
echo "   vercel --prod"
echo "   vercel env add REACT_APP_API_URL=$BACKEND_URL"
echo "   vercel --prod"
echo ""
echo "2. Configure Stripe Webhook:"
echo "   URL: $BACKEND_URL/api/webhooks/stripe"
echo "   Events: customer.subscription.created, updated, deleted"
echo "           invoice.payment_succeeded, failed"
echo "           charge.refunded"
echo ""
echo "3. Monitor Deployment:"
echo "   railway status"
echo "   railway logs"
echo ""
echo "4. Test Endpoints:"
echo "   curl $BACKEND_URL/health"
echo "   curl $BACKEND_URL/docs"
echo ""


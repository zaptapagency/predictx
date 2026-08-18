#!/bin/bash

# PredictX Automated Credentials Setup
# Use environment variables for non-interactive setup

set -e

echo "🔐 PredictX Automated Credentials Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Validate required variables
REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "SMTP_SERVER"
    "SMTP_PORT"
    "SMTP_USER"
    "SMTP_PASSWORD"
    "STRIPE_API_KEY"
    "STRIPE_WEBHOOK_SECRET"
    "STRIPE_PRO_PRICE_ID"
    "STRIPE_ENTERPRISE_PRICE_ID"
    "FRONTEND_URL"
)

echo -e "${YELLOW}Checking for required environment variables...${NC}"
echo ""

MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${YELLOW}⚠ Missing: $var${NC}"
        ((MISSING++))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo -e "${BLUE}To auto-configure, set these environment variables:${NC}"
    echo ""
    echo "# Database"
    echo "export DATABASE_URL='postgresql://user:pass@localhost:5432/predictx'"
    echo ""
    echo "# Redis"
    echo "export REDIS_URL='redis://localhost:6379'"
    echo ""
    echo "# JWT"
    echo "export JWT_SECRET_KEY='$(openssl rand -base64 48)'"
    echo ""
    echo "# SMTP (Gmail)"
    echo "export SMTP_SERVER='smtp.gmail.com'"
    echo "export SMTP_PORT='587'"
    echo "export SMTP_USER='your-email@gmail.com'"
    echo "export SMTP_PASSWORD='your-16-char-app-password'"
    echo ""
    echo "# Stripe"
    echo "export STRIPE_API_KEY='sk_test_your_key'"
    echo "export STRIPE_WEBHOOK_SECRET='whsec_your_secret'"
    echo "export STRIPE_PRO_PRICE_ID='price_pro_id'"
    echo "export STRIPE_ENTERPRISE_PRICE_ID='price_enterprise_id'"
    echo ""
    echo "# Frontend"
    echo "export FRONTEND_URL='http://localhost:3000'"
    echo ""
    echo "Then run: $0"
    exit 1
fi

echo -e "${GREEN}✓ All variables found${NC}"
echo ""

# Update .env file
echo -e "${BLUE}Updating .env file...${NC}"

sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
sed -i "s|REDIS_URL=.*|REDIS_URL=$REDIS_URL|" .env
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET_KEY|" .env
sed -i "s|SMTP_SERVER=.*|SMTP_SERVER=$SMTP_SERVER|" .env
sed -i "s|SMTP_PORT=.*|SMTP_PORT=$SMTP_PORT|" .env
sed -i "s|SMTP_USER=.*|SMTP_USER=$SMTP_USER|" .env
sed -i "s|SMTP_PASSWORD=.*|SMTP_PASSWORD=$SMTP_PASSWORD|" .env
sed -i "s|STRIPE_API_KEY=.*|STRIPE_API_KEY=$STRIPE_API_KEY|" .env
sed -i "s|STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET|" .env
sed -i "s|STRIPE_PRO_PRICE_ID=.*|STRIPE_PRO_PRICE_ID=$STRIPE_PRO_PRICE_ID|" .env
sed -i "s|STRIPE_ENTERPRISE_PRICE_ID=.*|STRIPE_ENTERPRISE_PRICE_ID=$STRIPE_ENTERPRISE_PRICE_ID|" .env
sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=$FRONTEND_URL|" .env

echo -e "${GREEN}✓ .env file updated${NC}"
echo ""

# Display configuration
echo -e "${BLUE}Configuration Summary:${NC}"
echo ""
echo "Database:    ${DATABASE_URL:0:50}..."
echo "Redis:       ${REDIS_URL:0:50}..."
echo "JWT Secret:  ${JWT_SECRET_KEY:0:30}..."
echo "SMTP Server: $SMTP_SERVER:$SMTP_PORT"
echo "SMTP User:   $SMTP_USER"
echo "Stripe Key:  ${STRIPE_API_KEY:0:30}..."
echo "Frontend:    $FRONTEND_URL"
echo ""

echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify .env: cat .env"
echo "  2. Deploy: ./deploy.sh"
echo "  3. Test: ./test-deployment.sh"
echo ""


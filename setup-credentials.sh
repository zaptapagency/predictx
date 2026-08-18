#!/bin/bash

# PredictX Credentials Setup Script

set -e

echo "🔐 PredictX Credentials Setup"
echo "=============================="
echo ""

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

echo -e "${BLUE}Enter your configuration details:${NC}"
echo ""

# Database
echo -e "${YELLOW}1. Database Configuration${NC}"
read -p "Database URL (postgresql://user:pass@host:5432/predictx): " DB_URL
DB_URL=${DB_URL:-"postgresql://predictx:predictx@localhost:5432/predictx"}

# Redis
echo ""
echo -e "${YELLOW}2. Redis Configuration${NC}"
read -p "Redis URL (redis://localhost:6379): " REDIS_URL
REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}

# JWT
echo ""
echo -e "${YELLOW}3. JWT Configuration${NC}"
echo "Generate a secure 64-character random key using: openssl rand -base64 32"
read -p "JWT Secret Key: " JWT_SECRET
if [ -z "$JWT_SECRET" ]; then
    echo "Generating random JWT secret..."
    JWT_SECRET=$(openssl rand -base64 48)
    echo "Generated: $JWT_SECRET"
fi

# SMTP
echo ""
echo -e "${YELLOW}4. Email (SMTP) Configuration${NC}"
echo "For Gmail:"
echo "  1. Enable 2-Factor Authentication"
echo "  2. Go to Account → Security → App passwords"
echo "  3. Generate a password for Mail"
read -p "SMTP Server (smtp.gmail.com): " SMTP_SERVER
SMTP_SERVER=${SMTP_SERVER:-"smtp.gmail.com"}
read -p "SMTP Port (587): " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-"587"}
read -p "SMTP Email: " SMTP_USER
read -sp "SMTP Password (16-char app password): " SMTP_PASSWORD
echo ""

# Stripe
echo ""
echo -e "${YELLOW}5. Stripe Configuration${NC}"
echo "Get your API keys from: https://dashboard.stripe.com/apikeys"
read -sp "Stripe API Key (sk_test_...): " STRIPE_API_KEY
echo ""
read -sp "Stripe Webhook Secret (whsec_...): " STRIPE_WEBHOOK_SECRET
echo ""
echo "Get price IDs from: https://dashboard.stripe.com/products"
read -p "Stripe Pro Price ID: " STRIPE_PRO_PRICE_ID
read -p "Stripe Enterprise Price ID: " STRIPE_ENTERPRISE_PRICE_ID

# Frontend URL
echo ""
echo -e "${YELLOW}6. Frontend Configuration${NC}"
read -p "Frontend URL (http://localhost:3000): " FRONTEND_URL
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}

# Update .env file
echo ""
echo -e "${BLUE}Updating .env file...${NC}"

sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|" .env
sed -i "s|REDIS_URL=.*|REDIS_URL=$REDIS_URL|" .env
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
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

# Verification
echo -e "${BLUE}Verifying configuration...${NC}"
echo ""

echo "Database:    $DB_URL"
echo "Redis:       $REDIS_URL"
echo "JWT Secret:  ${JWT_SECRET:0:20}..."
echo "SMTP Server: $SMTP_SERVER:$SMTP_PORT"
echo "SMTP User:   $SMTP_USER"
echo "Stripe Key:  ${STRIPE_API_KEY:0:20}..."
echo "Frontend:    $FRONTEND_URL"
echo ""

echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review .env file: cat .env"
echo "  2. Deploy: ./deploy.sh"
echo "  3. Test: ./test-deployment.sh"
echo ""


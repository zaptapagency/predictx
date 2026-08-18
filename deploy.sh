#!/bin/bash

# PredictX Deployment Script

set -e

echo "🚀 PredictX Deployment Starting..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Step 2: Setup environment
echo -e "${BLUE}Step 2: Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${RED}⚠ Please edit .env with your credentials${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configured${NC}"

# Step 3: Build images
echo -e "${BLUE}Step 3: Building Docker images...${NC}"
docker-compose build

echo -e "${GREEN}✓ Images built${NC}"

# Step 4: Start services
echo -e "${BLUE}Step 4: Starting services...${NC}"
docker-compose up -d

echo -e "${GREEN}✓ Services started${NC}"

# Step 5: Wait for database
echo -e "${BLUE}Step 5: Waiting for database...${NC}"
sleep 10

# Step 6: Run migrations
echo -e "${BLUE}Step 6: Running database migrations...${NC}"
docker-compose exec -T backend alembic upgrade head

echo -e "${GREEN}✓ Migrations completed${NC}"

# Step 7: Health checks
echo -e "${BLUE}Step 7: Running health checks...${NC}"
sleep 5

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}✗ Frontend health check failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Access your application:"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}Backend:${NC} http://localhost:8000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""

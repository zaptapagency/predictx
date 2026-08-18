#!/bin/bash

# PredictX Deployment Test Script

set -e

echo "🧪 PredictX Deployment Tests"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0
PASSED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Testing $name... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED (HTTP $status)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED (Expected $expected_status, got $status)${NC}"
        ((FAILED++))
    fi
}

# Get base URLs
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}

echo -e "${BLUE}Backend URL: $BACKEND_URL${NC}"
echo -e "${BLUE}Frontend URL: $FRONTEND_URL${NC}"
echo ""

# Backend Tests
echo -e "${YELLOW}Backend Tests:${NC}"
test_endpoint "Health Check" "$BACKEND_URL/health" "200"
test_endpoint "API Docs" "$BACKEND_URL/docs" "200"
test_endpoint "OpenAPI Schema" "$BACKEND_URL/openapi.json" "200"

# Frontend Tests
echo ""
echo -e "${YELLOW}Frontend Tests:${NC}"
test_endpoint "Homepage" "$FRONTEND_URL/" "200"
test_endpoint "Login Page" "$FRONTEND_URL/login" "200"
test_endpoint "Signup Page" "$FRONTEND_URL/signup" "200"

# Database Tests
echo ""
echo -e "${YELLOW}Database Tests:${NC}"

if command -v psql &> /dev/null; then
    echo -n "Testing Database Connection... "
    
    if psql -U predictx -d predictx -c "SELECT 1" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
fi

# API Tests
echo ""
echo -e "${YELLOW}API Tests:${NC}"

# Test signup
echo -n "Testing POST /api/auth/signup... "
response=$(curl -s -X POST "$BACKEND_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123",
    "full_name": "Test User"
  }' 2>/dev/null)

if echo "$response" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test login
echo -n "Testing POST /api/auth/login... "
response=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }' 2>/dev/null)

if echo "$response" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
    
    # Extract token for further tests
    TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test protected endpoint
if [ ! -z "$TOKEN" ]; then
    echo -n "Testing GET /api/users/me (Protected)... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      "$BACKEND_URL/api/users/me" 2>/dev/null)
    
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED (HTTP $status)${NC}"
        ((FAILED++))
    fi
fi

# Docker Tests
echo ""
echo -e "${YELLOW}Docker Tests:${NC}"

if command -v docker &> /dev/null; then
    echo -n "Testing Backend Container... "
    if docker ps | grep -q predictx_backend; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        ((FAILED++))
    fi
    
    echo -n "Testing Frontend Container... "
    if docker ps | grep -q predictx_frontend; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        ((FAILED++))
    fi
    
    echo -n "Testing Database Container... "
    if docker ps | grep -q predictx_postgres; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        ((FAILED++))
    fi
fi

# Summary
echo ""
echo "================================"
echo -e "Tests Passed:  ${GREEN}$PASSED${NC}"
echo -e "Tests Failed:  ${RED}$FAILED${NC}"
echo "================================"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Deployment is ready. Next steps:"
    echo "  1. Test signup flow manually: $FRONTEND_URL/signup"
    echo "  2. Test predictions: $FRONTEND_URL/predictions"
    echo "  3. Monitor logs: docker-compose logs -f"
    echo "  4. Check metrics: $BACKEND_URL/docs"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs -f backend"
    echo "  2. Check database: docker-compose exec postgres psql -U predictx -d predictx"
    echo "  3. Verify .env: cat .env"
    exit 1
fi


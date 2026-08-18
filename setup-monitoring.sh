#!/bin/bash

# PredictX Monitoring Setup Script

echo "📊 PredictX Monitoring Setup"
echo "============================"
echo ""

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}This script sets up monitoring for PredictX${NC}"
echo ""

# Check if Sentry is configured
echo -e "${BLUE}1. Error Tracking (Optional - Sentry)${NC}"
read -p "Do you want to setup Sentry for error tracking? (y/n): " setup_sentry

if [ "$setup_sentry" = "y" ]; then
    echo "Visit: https://sentry.io/signup"
    echo "Create a project for Django/FastAPI"
    read -p "Enter your Sentry DSN: " SENTRY_DSN
    
    if [ ! -z "$SENTRY_DSN" ]; then
        sed -i "s|SENTRY_DSN=.*|SENTRY_DSN=$SENTRY_DSN|" .env
        echo -e "${GREEN}✓ Sentry configured${NC}"
    fi
fi

echo ""

# Docker monitoring
echo -e "${BLUE}2. Docker Container Monitoring${NC}"
echo "Monitor container health and resource usage:"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo "  docker-compose logs -f postgres"
echo ""
echo "View stats:"
echo "  docker stats predictx_backend"
echo "  docker stats predictx_postgres"
echo ""

# Health check endpoints
echo -e "${BLUE}3. Health Check Endpoints${NC}"
echo ""
echo "Backend health:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Database health:"
echo "  docker-compose exec postgres psql -U predictx -d predictx -c 'SELECT 1'"
echo ""
echo "Redis health:"
echo "  docker-compose exec redis redis-cli ping"
echo ""

# Prometheus setup (optional)
echo -e "${BLUE}4. Prometheus Monitoring (Optional)${NC}"
read -p "Do you want to setup Prometheus? (y/n): " setup_prometheus

if [ "$setup_prometheus" = "y" ]; then
    echo "Creating prometheus.yml..."
    
    mkdir -p monitoring
    
    cat > monitoring/prometheus.yml << 'PROM'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
PROM

    echo -e "${GREEN}✓ prometheus.yml created${NC}"
    echo ""
    echo "Add to docker-compose.yml:"
    echo "  prometheus:"
    echo "    image: prom/prometheus"
    echo "    ports:"
    echo "      - '9090:9090'"
    echo "    volumes:"
    echo "      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"
fi

echo ""

# Logging setup
echo -e "${BLUE}5. Logging Configuration${NC}"
echo ""
echo "Logs are stored in:"
echo "  Backend: docker-compose logs backend"
echo "  Frontend: docker-compose logs frontend"
echo "  Database: docker-compose logs postgres"
echo ""
echo "For persistent logs, configure Docker logging driver:"
echo "  Driver: json-file (default)"
echo "  Location: /var/lib/docker/containers/<id>/<id>-json.log"
echo ""

# Uptime monitoring
echo -e "${BLUE}6. Uptime Monitoring (Optional)${NC}"
echo "Recommended services:"
echo "  - UptimeRobot (https://uptimerobot.com) - Free"
echo "  - Pingdom (https://www.pingdom.com) - Paid"
echo "  - StatusPage (https://www.statuspage.io) - Paid"
echo ""
echo "Monitor your backend:"
echo "  URL: https://your-domain.com/health"
echo "  Interval: 5 minutes"
echo "  Alert if down: Yes"
echo ""

# Summary
echo -e "${GREEN}✅ Monitoring setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start monitoring: docker-compose up -d"
echo "  2. Check logs: docker-compose logs -f"
echo "  3. View health: curl http://localhost:8000/health"
echo "  4. Setup uptime alerts"
echo "  5. Configure error tracking (Sentry)"
echo ""


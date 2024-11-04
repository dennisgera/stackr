#!/bin/bash
# test.sh

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting test environment...${NC}"

# Ensure we're starting fresh
echo -e "${YELLOW}Cleaning up any existing test environment...${NC}"
docker-compose -f docker-compose.test.yml down -v

# Start the test environment
echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose -f docker-compose.test.yml up --build -d

# Function to check if a container is healthy
check_container_health() {
    local container_name=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $container_name to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        health_status=$(docker inspect --format='{{.State.Health.Status}}' stackr-$container_name-1 2>/dev/null)
        container_running=$(docker inspect --format='{{.State.Running}}' stackr-$container_name-1 2>/dev/null)
        
        if [ "$health_status" = "healthy" ]; then
            echo -e "${GREEN}✅ $container_name is healthy${NC}"
            return 0
        elif [ "$health_status" = "unhealthy" ] || [ "$container_running" = "false" ]; then
            echo -e "${RED}❌ $container_name is not healthy or not running${NC}"
            echo -e "${YELLOW}Container logs:${NC}"
            docker logs stackr-$container_name-1
            return 1
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}❌ Timeout waiting for $container_name to be healthy${NC}"
    docker logs stackr-$container_name-1
    return 1
}

# Check container health
check_container_health "db-test" || exit 1
check_container_health "backend-test" || exit 1

echo -e "${YELLOW}⏳ Waiting for all services to be fully ready...${NC}"
sleep 10

# Test functions
test_endpoint() {
    local endpoint=$1
    local name=$2
    local response=$(python3 -c "
import urllib.request
import urllib.error
try:
    code = urllib.request.urlopen('$endpoint').getcode()
    print(code)
except urllib.error.URLError as e:
    print(e.code if hasattr(e, 'code') else 500)
")
    
    echo -e "${YELLOW}🔍 Testing $name...${NC}"
    if [ "$response" == "200" ]; then
        echo -e "${GREEN}✅ $name check passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $name check failed (status: $response)${NC}"
        echo "Trying to get detailed response from $endpoint:"
        python3 -c "
import urllib.request
try:
    response = urllib.request.urlopen('$endpoint')
    print(response.read().decode())
except Exception as e:
    print('Error:', e)
"
        return 1
    fi
}

# Run tests
test_endpoint "http://localhost:8000/health" "Health endpoint" || FAILED=1
test_endpoint "http://localhost:8501" "Frontend" || FAILED=1

# Show container logs if any test failed
if [ "$FAILED" == "1" ]; then
    echo -e "${RED}Some tests failed. Showing container logs:${NC}"
    echo -e "${YELLOW}Backend logs:${NC}"
    docker-compose -f docker-compose.test.yml logs backend-test
    echo -e "${YELLOW}Frontend logs:${NC}"
    docker-compose -f docker-compose.test.yml logs frontend-test
fi

echo -e "
${GREEN}🔍 Services are running and ready for manual testing:${NC}
- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- API Documentation: http://localhost:8000/docs

To stop the services, run:
${YELLOW}docker-compose -f docker-compose.test.yml down -v${NC}
"

if [ "$FAILED" == "1" ]; then
    exit 1
fi
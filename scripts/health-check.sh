#!/bin/bash

# TheraBot Health Check Script
set -e

# Configuration
BASE_URL="${1:-http://localhost:5000}"
TIMEOUT=10
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        *)
            BASE_URL="$1"
            shift
            ;;
    esac
done

echo "🏥 TheraBot Health Check"
echo "🌐 URL: $BASE_URL"
echo " Timeout: ${TIMEOUT}s"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -n "Checking $description... "
    
    if [ "$VERBOSE" = true ]; then
        echo ""
    fi
    
    response=$(curl -s -w "%{http_code}" --connect-timeout $TIMEOUT "$BASE_URL$endpoint" -o /tmp/health_response 2>/dev/null) || {
        echo -e "${RED}FAILED${NC} - Connection failed"
        return 1
    }
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}OK${NC} ($status_code)"
        if [ "$VERBOSE" = true ]; then
            echo "Response: $(cat /tmp/health_response | head -c 200)"
            echo ""
        fi
        return 0
    else
        echo -e "${RED}FAILED${NC} ($status_code, expected $expected_status)"
        if [ "$VERBOSE" = true ]; then
            echo "Response: $(cat /tmp/health_response | head -c 200)"
            echo ""
        fi
        return 1
    fi
}

# Function to check Docker containers
check_docker() {
    echo -e "${BLUE}🐳 Docker Container Status:${NC}"
    
    if command -v docker &> /dev/null; then
        if docker compose ps --services &> /dev/null; then
            docker compose ps
        elif docker-compose ps &> /dev/null; then
            docker-compose ps
        else
            echo "No Docker Compose found"
        fi
    else
        echo "Docker not available"
    fi
    echo ""
}

# Function to check system resources
check_resources() {
    echo -e "${BLUE}💻 System Resources:${NC}"
    
    if command -v free &> /dev/null; then
        echo "Memory usage:"
        free -h | grep -E "Mem:|Swap:"
    fi
    
    if command -v df &> /dev/null; then
        echo "Disk usage:"
        df -h / | tail -1
    fi
    
    echo "Load average:"
    uptime
    echo ""
}

# Function to check Ollama
check_ollama() {
    echo -e "${BLUE}🦙 Ollama Service:${NC}"
    
    if curl -s --connect-timeout 5 http://localhost:11434/api/tags > /tmp/ollama_response 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Ollama is running"
        if [ "$VERBOSE" = true ]; then
            echo "Available models:"
            cat /tmp/ollama_response | python3 -m json.tool 2>/dev/null || cat /tmp/ollama_response
        fi
    else
        echo -e "${RED}✗${NC} Ollama is not responding"
    fi
    echo ""
}

# Main health checks
echo -e "${BLUE}🔍 Endpoint Checks:${NC}"
check_endpoint "/" 200 "Main page"

# Check if it's a streaming endpoint
echo -n "Checking chat endpoint... "
if curl -s --connect-timeout $TIMEOUT -X POST \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}' \
    "$BASE_URL/chat" > /tmp/chat_response 2>/dev/null; then
    echo -e "${GREEN}OK${NC} (Chat endpoint responding)"
else
    echo -e "${RED}FAILED${NC} (Chat endpoint not responding)"
fi

echo ""

# Additional checks
check_docker
check_resources
check_ollama

# Summary
echo -e "${BLUE}📊 Health Check Summary:${NC}"
if check_endpoint "/" 200 "Overall health" > /dev/null 2>&1; then
    echo -e "Status: ${GREEN}HEALTHY${NC} ✓"
    exit 0
else
    echo -e "Status: ${RED}UNHEALTHY${NC} ✗"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Check if all containers are running: docker-compose ps"
    echo "2. Check logs: docker-compose logs -f"
    echo "3. Verify Ollama is running: curl http://localhost:11434/api/tags"
    echo "4. Check system resources: free -h && df -h"
    exit 1
fi

# Cleanup
rm -f /tmp/health_response /tmp/chat_response /tmp/ollama_response
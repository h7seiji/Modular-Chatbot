#!/bin/bash

# Test script to verify the FastAPI backend works with Docker Compose

echo "🚀 Testing FastAPI backend with Docker Compose..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "URL: $url"
    
    if [ -n "$data" ]; then
        echo "Data: $data"
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X "$method" "$url")
    fi
    
    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n1 | sed 's/.*HTTP_CODE://')
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Success (HTTP $http_code)${NC}"
        echo "Response: $body" | jq . 2>/dev/null || echo "Response: $body"
    else
        echo -e "${RED}❌ Failed (HTTP $http_code)${NC}"
        echo "Response: $body"
        return 1
    fi
    
    return 0
}

# Wait for services to be ready
echo "Waiting for backend service to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend service is ready!${NC}"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Test health endpoint
test_endpoint "GET" "http://localhost:8000/health" "" "Health check endpoint"

# Test chat endpoint with math query
math_data='{"message": "What is 5 + 3?", "user_id": "test_user_123", "conversation_id": "test_conv_456"}'
test_endpoint "POST" "http://localhost:8000/chat" "$math_data" "Chat endpoint with math query"

# Test chat endpoint with knowledge query
knowledge_data='{"message": "What are the InfinitePay card machine fees?", "user_id": "test_user_789", "conversation_id": "test_conv_101"}'
test_endpoint "POST" "http://localhost:8000/chat" "$knowledge_data" "Chat endpoint with knowledge query"

# Test input validation
invalid_data='{"message": "", "user_id": "test_user", "conversation_id": "test_conv"}'
echo -e "\n${YELLOW}Testing: Input validation (should fail)${NC}"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X "POST" -H "Content-Type: application/json" -d "$invalid_data" "http://localhost:8000/chat")
http_code=$(echo "$response" | tail -n1 | sed 's/.*HTTP_CODE://')

if [ "$http_code" -eq 400 ]; then
    echo -e "${GREEN}✅ Validation test passed (HTTP $http_code)${NC}"
else
    echo -e "${RED}❌ Validation test failed (HTTP $http_code)${NC}"
fi

echo -e "\n🎉 API testing completed!"
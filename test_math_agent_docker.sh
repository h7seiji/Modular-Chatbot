#!/bin/bash

# Test script for MathAgent in Docker environment
echo "🧮 Testing MathAgent in Docker Environment"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🐳 Docker is running"

# Build and start the services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test health endpoint
echo "🏥 Testing health endpoint..."
health_response=$(curl -s http://localhost:8000/health)
if [[ $? -eq 0 ]]; then
    echo "✅ Health endpoint accessible"
    echo "   Response: $health_response"
else
    echo "❌ Health endpoint not accessible"
fi

# Test mathematical queries
echo ""
echo "🧮 Testing mathematical queries..."

# Test 1: Simple addition
echo "📝 Test 1: Simple addition"
response1=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 5 + 3?",
    "user_id": "test_user_1",
    "conversation_id": "test_conv_1"
  }')

if [[ $? -eq 0 ]]; then
    echo "✅ Addition query successful"
    echo "   Response: $response1" | jq '.' 2>/dev/null || echo "   Response: $response1"
else
    echo "❌ Addition query failed"
fi

# Test 2: Multiplication
echo ""
echo "📝 Test 2: Multiplication"
response2=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much is 65 x 3.11?",
    "user_id": "test_user_2",
    "conversation_id": "test_conv_2"
  }')

if [[ $? -eq 0 ]]; then
    echo "✅ Multiplication query successful"
    echo "   Response: $response2" | jq '.' 2>/dev/null || echo "   Response: $response2"
else
    echo "❌ Multiplication query failed"
fi

# Test 3: Complex expression
echo ""
echo "📝 Test 3: Complex expression"
response3=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate (42 * 2) / 6",
    "user_id": "test_user_3",
    "conversation_id": "test_conv_3"
  }')

if [[ $? -eq 0 ]]; then
    echo "✅ Complex expression query successful"
    echo "   Response: $response3" | jq '.' 2>/dev/null || echo "   Response: $response3"
else
    echo "❌ Complex expression query failed"
fi

# Test 4: Non-mathematical query (should not go to MathAgent)
echo ""
echo "📝 Test 4: Non-mathematical query"
response4=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are InfinitePay fees?",
    "user_id": "test_user_4",
    "conversation_id": "test_conv_4"
  }')

if [[ $? -eq 0 ]]; then
    echo "✅ Non-mathematical query successful"
    echo "   Response: $response4" | jq '.' 2>/dev/null || echo "   Response: $response4"
else
    echo "❌ Non-mathematical query failed"
fi

echo ""
echo "📊 Docker testing completed!"
echo "💡 Check the responses above to verify MathAgent is working correctly"
echo ""
echo "🛑 To stop the services, run: docker-compose down"
#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI backend is working correctly.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "agents_registered" in data
    
    print("✅ Health endpoint test passed")


def test_chat_endpoint_math_query():
    """Test the chat endpoint with a mathematical query."""
    request_data = {
        "message": "What is 5 + 3?",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456"
    }
    
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "source_agent_response" in data
    assert "agent_workflow" in data
    
    # Check that MathAgent was selected
    assert "MathAgent" in data["source_agent_response"]
    assert len(data["agent_workflow"]) == 2
    assert data["agent_workflow"][0]["agent"] == "RouterAgent"
    assert "MathAgent" in data["agent_workflow"][1]["agent"]
    
    print("✅ Math query test passed")
    print(f"   Response: {data['response']}")


def test_chat_endpoint_knowledge_query():
    """Test the chat endpoint with a knowledge query."""
    request_data = {
        "message": "What are the InfinitePay card machine fees?",
        "user_id": "test_user_789",
        "conversation_id": "test_conv_101"
    }
    
    response = client.post("/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "source_agent_response" in data
    assert "agent_workflow" in data
    
    # Check that KnowledgeAgent was selected
    assert "KnowledgeAgent" in data["source_agent_response"]
    assert len(data["agent_workflow"]) == 2
    assert data["agent_workflow"][0]["agent"] == "RouterAgent"
    assert "KnowledgeAgent" in data["agent_workflow"][1]["agent"]
    
    print("✅ Knowledge query test passed")
    print(f"   Response: {data['response']}")


def test_chat_endpoint_validation():
    """Test input validation on the chat endpoint."""
    # Test empty message
    response = client.post("/chat", json={
        "message": "",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    })
    assert response.status_code == 400
    
    # Test invalid user_id
    response = client.post("/chat", json={
        "message": "Hello",
        "user_id": "invalid@user",
        "conversation_id": "test_conv"
    })
    assert response.status_code == 400
    
    # Test invalid conversation_id
    response = client.post("/chat", json={
        "message": "Hello",
        "user_id": "test_user",
        "conversation_id": "invalid@conv"
    })
    assert response.status_code == 400
    
    print("✅ Input validation tests passed")


def run_all_tests():
    """Run all tests."""
    print("🚀 Starting API tests...")
    
    try:
        test_health_endpoint()
        test_chat_endpoint_math_query()
        test_chat_endpoint_knowledge_query()
        test_chat_endpoint_validation()
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
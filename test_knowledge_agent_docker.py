#!/usr/bin/env python3
"""
Test script to verify KnowledgeAgent functionality in Docker environment.

This script tests the KnowledgeAgent by making HTTP requests to the Docker container.
"""
import requests
import json
import time
import sys


def test_knowledge_agent_endpoint():
    """Test the KnowledgeAgent through the /chat endpoint."""
    
    # Docker container URL
    base_url = "http://localhost:8000"
    
    print("🚀 Testing KnowledgeAgent in Docker Environment")
    print("=" * 50)
    
    # Test health endpoint first
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Agents registered: {health_data.get('agents_registered')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Docker container: {str(e)}")
        print("   Make sure the Docker container is running on port 8000")
        return False
    
    # Test knowledge queries
    knowledge_queries = [
        "What are InfinitePay card machine fees?",
        "How do I set up my InfinitePay account?",
        "Tell me about payment processing services",
        "What is PIX payment?",
        "How does InfinitePay work?",
    ]
    
    print(f"\nTesting {len(knowledge_queries)} knowledge queries...")
    
    for i, query in enumerate(knowledge_queries, 1):
        print(f"\n{i}. Testing query: '{query}'")
        
        # Prepare request
        chat_request = {
            "message": query,
            "user_id": "test-user-123",
            "conversation_id": f"test-conv-{i}"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response received in {response_time:.2f}s")
                print(f"      Source agent: {data.get('source_agent_response', 'Unknown')}")
                
                # Check if KnowledgeAgent was used
                workflow = data.get('agent_workflow', [])
                knowledge_agent_used = any('KnowledgeAgent' in str(step) for step in workflow)
                
                if knowledge_agent_used:
                    print(f"      ✅ KnowledgeAgent was used")
                else:
                    print(f"      ⚠️  KnowledgeAgent was not used (routed to different agent)")
                
                # Show response preview
                response_content = data.get('response', '')
                preview = response_content[:100] + "..." if len(response_content) > 100 else response_content
                print(f"      Response: {preview}")
                
                # Show workflow
                print(f"      Workflow: {workflow}")
                
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"      Error: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timed out after 30 seconds")
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
    
    # Test mathematical query (should NOT go to KnowledgeAgent)
    print(f"\n{len(knowledge_queries) + 1}. Testing mathematical query (should go to MathAgent):")
    math_query = "What is 5 + 3?"
    print(f"   Query: '{math_query}'")
    
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={
                "message": math_query,
                "user_id": "test-user-123",
                "conversation_id": "test-conv-math"
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            workflow = data.get('agent_workflow', [])
            math_agent_used = any('MathAgent' in str(step) for step in workflow)
            
            if math_agent_used:
                print(f"   ✅ Correctly routed to MathAgent")
            else:
                print(f"   ⚠️  Not routed to MathAgent: {workflow}")
        else:
            print(f"   ❌ Math query failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Math query error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 KnowledgeAgent Docker Tests Completed")
    return True


if __name__ == "__main__":
    success = test_knowledge_agent_endpoint()
    sys.exit(0 if success else 1)
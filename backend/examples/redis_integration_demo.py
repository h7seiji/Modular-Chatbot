#!/usr/bin/env python3
"""
Redis integration demonstration script showing conversation history and logging functionality.
"""
import sys
import os
import time
import requests
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_redis_integration():
    """Test Redis integration through the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Redis Integration Demo")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Health check passed")
            print(f"  Redis available: {health_data.get('redis_available', False)}")
            print(f"  Agents registered: {health_data.get('agents_registered', 0)}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test 2: Send chat messages to create conversation history
    print("\n2. Testing conversation history storage...")
    conversation_id = f"demo-conv-{int(time.time())}"
    user_id = "demo-user-123"
    
    messages = [
        "Hello! I need help with some calculations.",
        "What is 65 * 3.11?",
        "Can you also help me understand InfinitePay fees?"
    ]
    
    for i, message in enumerate(messages):
        print(f"  Sending message {i+1}: {message[:30]}...")
        try:
            response = requests.post(
                f"{base_url}/chat",
                json={
                    "message": message,
                    "userId": user_id,
                    "conversationId": conversation_id
                }
            )
            if response.status_code == 200:
                chat_data = response.json()
                print(f"    ✓ Response from {chat_data.get('source_agent_response', 'Unknown')}")
            else:
                print(f"    ✗ Chat request failed: {response.status_code}")
                print(f"    Error: {response.text}")
        except Exception as e:
            print(f"    ✗ Chat request error: {e}")
    
    # Test 3: Retrieve conversation history
    print(f"\n3. Testing conversation retrieval...")
    try:
        response = requests.get(f"{base_url}/conversations/{conversation_id}")
        if response.status_code == 200:
            conv_data = response.json()
            print(f"✓ Retrieved conversation with {conv_data['message_count']} messages")
            print(f"  User ID: {conv_data['user_id']}")
            print(f"  Created: {conv_data['timestamp']}")
            for i, msg in enumerate(conv_data['messages'][:3]):  # Show first 3 messages
                print(f"    {i+1}. [{msg['sender']}] {msg['content'][:50]}...")
        else:
            print(f"✗ Conversation retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Conversation retrieval error: {e}")
    
    # Test 4: Get user conversations
    print(f"\n4. Testing user conversation list...")
    try:
        response = requests.get(f"{base_url}/conversations/user/{user_id}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✓ Found {user_data['conversation_count']} conversations for user")
            print(f"  Conversation IDs: {user_data['conversation_ids']}")
        else:
            print(f"✗ User conversations failed: {response.status_code}")
    except Exception as e:
        print(f"✗ User conversations error: {e}")
    
    # Test 5: Check Redis logs
    print(f"\n5. Testing Redis logging...")
    try:
        response = requests.get(f"{base_url}/logs?component=chat&limit=10")
        if response.status_code == 200:
            logs_data = response.json()
            print(f"✓ Retrieved {logs_data['count']} chat logs")
            for log in logs_data['logs'][:3]:  # Show first 3 logs
                print(f"    [{log['level']}] {log['message']}")
        else:
            print(f"✗ Log retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Log retrieval error: {e}")
    
    # Test 6: Check log statistics
    print(f"\n6. Testing log statistics...")
    try:
        response = requests.get(f"{base_url}/logs/stats?component=chat")
        if response.status_code == 200:
            stats_data = response.json()
            print(f"✓ Log statistics retrieved")
            print(f"  Total logs: {stats_data.get('total', 0)}")
            for level, count in stats_data.get('levels', {}).items():
                if count > 0:
                    print(f"    {level}: {count}")
        else:
            print(f"✗ Log stats failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Log stats error: {e}")
    
    print("\n" + "=" * 50)
    print("✓ Redis integration demo completed!")
    print("\nThis demo showed:")
    print("  • Redis health check integration")
    print("  • Conversation history storage and retrieval")
    print("  • User conversation management")
    print("  • Redis-based logging system")
    print("  • Log statistics and monitoring")
    
    return True

def main():
    """Run the Redis integration demonstration."""
    print("Redis Integration Demo")
    print("Make sure the backend server is running on http://localhost:8000")
    print("and Redis is available before running this demo.")
    print()
    
    try:
        success = test_redis_integration()
        if success:
            print("\n✓ All tests completed successfully!")
        else:
            print("\n✗ Some tests failed. Check the output above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


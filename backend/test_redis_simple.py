#!/usr/bin/env python3
"""
Simple test script to verify Redis client functionality.
"""
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.services.redis_client import RedisClient
    from backend.models.core import ConversationContext, Message
    print("✓ Successfully imported Redis client and models")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_redis_client_creation():
    """Test Redis client creation."""
    try:
        client = RedisClient(host="localhost", port=6379, db=15)
        print("✓ Redis client created successfully")
        return client
    except Exception as e:
        print(f"✗ Failed to create Redis client: {e}")
        return None

def test_conversation_creation():
    """Test conversation creation."""
    try:
        messages = [
            Message(
                content="Hello, test!",
                sender="user",
                timestamp=datetime.utcnow(),
                agent_type=None
            )
        ]
        
        conversation = ConversationContext(
            conversation_id="test-conv-simple",
            user_id="test-user-simple",
            timestamp=datetime.utcnow(),
            message_history=messages
        )
        print("✓ Conversation created successfully")
        return conversation
    except Exception as e:
        print(f"✗ Failed to create conversation: {e}")
        return None

def test_key_generation(client):
    """Test key generation methods."""
    try:
        conv_key = client._get_conversation_key("test-123")
        user_key = client._get_user_conversations_key("user-456")
        
        assert conv_key == "conversation:test-123"
        assert user_key == "user_conversations:user-456"
        
        print("✓ Key generation works correctly")
        return True
    except Exception as e:
        print(f"✗ Key generation failed: {e}")
        return False

def main():
    """Run simple tests."""
    print("Running simple Redis client tests...")
    print("-" * 40)
    
    # Test imports and creation
    client = test_redis_client_creation()
    if not client:
        return False
    
    conversation = test_conversation_creation()
    if not conversation:
        return False
    
    # Test key generation
    if not test_key_generation(client):
        return False
    
    print("-" * 40)
    print("✓ All simple tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
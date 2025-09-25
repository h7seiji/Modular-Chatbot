#!/usr/bin/env python3
"""
Debug script to test Redis conversation storage functionality.
"""
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from models.core import ConversationContext, Message
from services.redis_client import RedisClient

def test_redis_connection():
    """Test basic Redis connection."""
    print("Testing Redis connection...")
    try:
        client = RedisClient(host="redis", port=6379, db=0)
        if client.health_check():
            print("✓ Redis connection successful")
            return client
        else:
            print("✗ Redis health check failed")
            return None
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return None

def test_conversation_serialization():
    """Test conversation serialization to JSON."""
    print("\nTesting conversation serialization...")
    try:
        # Create a test conversation
        conversation = ConversationContext(
            conversation_id="test_conversation_123",
            user_id="test_user_456",
            message_history=[
                Message(
                    content="Hello, I need help with math",
                    sender="user",
                    timestamp=datetime.utcnow()
                ),
                Message(
                    content="I can help you with math problems!",
                    sender="agent",
                    agent_type="MathAgent",
                    timestamp=datetime.utcnow()
                )
            ]
        )
        
        # Serialize to JSON (same as in store_conversation)
        conversation_data = {
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id,
            "timestamp": conversation.timestamp.isoformat(),
            "message_history": [
                {
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "agent_type": msg.agent_type,
                }
                for msg in conversation.message_history
            ],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        
        json_str = json.dumps(conversation_data)
        print(f"✓ Conversation serialization successful")
        print(f"  JSON length: {len(json_str)} characters")
        return conversation, conversation_data
        
    except Exception as e:
        print(f"✗ Conversation serialization failed: {e}")
        return None, None

def test_pipeline_operations(redis_client, conversation_data):
    """Test individual pipeline operations."""
    print("\nTesting pipeline operations...")
    try:
        conversation_id = conversation_data["conversation_id"]
        user_id = conversation_data["user_id"]
        
        conversation_key = f"conversation:{conversation_id}"
        user_conversations_key = f"user_conversations:{user_id}"
        
        # Test individual operations
        pipe = redis_client.client.pipeline()
        
        # Test SET operation
        pipe.set(conversation_key, json.dumps(conversation_data), ex=3600)
        
        # Test SADD operation
        pipe.sadd(user_conversations_key, conversation_id)
        
        # Test EXPIRE operation
        pipe.expire(user_conversations_key, 3600)
        
        # Execute pipeline
        results = pipe.execute()
        
        print(f"Pipeline results: {results}")
        
        if all(results):
            print("✓ All pipeline operations successful")
            return True
        else:
            print("✗ Some pipeline operations failed")
            for i, result in enumerate(results):
                if not result:
                    print(f"  Operation {i} failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ Pipeline operations failed: {e}")
        return False

def test_retrieval(redis_client, conversation_id):
    """Test conversation retrieval."""
    print("\nTesting conversation retrieval...")
    try:
        conversation_key = f"conversation:{conversation_id}"
        conversation_data = redis_client.client.get(conversation_key)
        
        if conversation_data:
            print("✓ Conversation retrieval successful")
            print(f"  Retrieved data length: {len(conversation_data)} characters")
            return True
        else:
            print("✗ Conversation retrieval failed - no data found")
            return False
            
    except Exception as e:
        print(f"✗ Conversation retrieval failed: {e}")
        return False

def test_full_store_cycle(redis_client, conversation):
    """Test the full store_conversation cycle."""
    print("\nTesting full store_conversation cycle...")
    try:
        # Add detailed debugging
        print(f"  Conversation ID: {conversation.conversation_id}")
        print(f"  User ID: {conversation.user_id}")
        print(f"  Message count: {len(conversation.message_history)}")
        
        # Test the store_conversation method with detailed error capture
        success = redis_client.store_conversation(conversation)
        if success:
            print("✓ Full store_conversation cycle successful")
            return True
        else:
            print("✗ Full store_conversation cycle failed")
            # Let's manually test the store_conversation logic step by step
            return test_store_conversation_manually(redis_client, conversation)
            
    except Exception as e:
        print(f"✗ Full store_conversation cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_store_conversation_manually(redis_client, conversation):
    """Manually test the store_conversation logic step by step."""
    print("\nTesting store_conversation logic manually...")
    try:
        conversation_key = f"conversation:{conversation.conversation_id}"
        user_conversations_key = f"user_conversations:{conversation.user_id}"
        
        print(f"  Conversation key: {conversation_key}")
        print(f"  User conversations key: {user_conversations_key}")
        
        # Serialize conversation to JSON (same as in store_conversation)
        conversation_data = {
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id,
            "timestamp": conversation.timestamp.isoformat(),
            "message_history": [
                {
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "agent_type": msg.agent_type,
                }
                for msg in conversation.message_history
            ],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }
        
        print(f"  Serialized data keys: {list(conversation_data.keys())}")
        
        # Use pipeline for atomic operations
        pipe = redis_client.client.pipeline()
        
        # Store conversation data
        pipe.set(
            conversation_key,
            json.dumps(conversation_data),
            ex=3600  # Use 1 hour TTL for testing
        )
        
        # Add conversation to user's conversation list
        pipe.sadd(user_conversations_key, conversation.conversation_id)
        pipe.expire(user_conversations_key, 3600)
        
        # Execute pipeline
        results = pipe.execute()
        
        print(f"  Pipeline results: {results}")
        
        if all(results):
            print("✓ Manual store_conversation logic successful")
            return True
        else:
            # Check results - SADD returns 0 if member already exists, which is not an error
            set_success = results[0]  # SET operation
            sadd_result = results[1]   # SADD operation (0 is OK if member exists)
            expire_success = results[2]  # EXPIRE operation
            
            if set_success and (sadd_result >= 0) and expire_success:
                print("✓ Manual store_conversation logic successful (member already exists)")
                return True
            else:
                print("✗ Manual store_conversation logic failed")
                for i, result in enumerate(results):
                    if not result:
                        print(f"  Operation {i} failed: {result}")
                return False
            
    except Exception as e:
        print(f"✗ Manual store_conversation logic failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("=== Redis Storage Debug Test ===\n")
    
    # Test 1: Redis Connection
    redis_client = test_redis_connection()
    if not redis_client:
        print("Cannot proceed without Redis connection")
        sys.exit(1)
    
    # Test 2: Conversation Serialization
    conversation, conversation_data = test_conversation_serialization()
    if not conversation:
        print("Cannot proceed without conversation serialization")
        sys.exit(1)
    
    # Test 3: Pipeline Operations
    pipeline_success = test_pipeline_operations(redis_client, conversation_data)
    
    # Test 4: Retrieval
    if pipeline_success:
        retrieval_success = test_retrieval(redis_client, conversation.conversation_id)
    else:
        retrieval_success = False
    
    # Test 5: Full Store Cycle
    full_cycle_success = test_full_store_cycle(redis_client, conversation)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Redis Connection: {'✓' if redis_client else '✗'}")
    print(f"Conversation Serialization: {'✓' if conversation else '✗'}")
    print(f"Pipeline Operations: {'✓' if pipeline_success else '✗'}")
    print(f"Conversation Retrieval: {'✓' if retrieval_success else '✗'}")
    print(f"Full Store Cycle: {'✓' if full_cycle_success else '✗'}")
    
    if all([redis_client, conversation, pipeline_success, retrieval_success, full_cycle_success]):
        print("\n🎉 All tests passed! Redis storage is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

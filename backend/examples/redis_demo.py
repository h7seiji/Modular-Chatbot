#!/usr/bin/env python3
"""
Redis client demonstration script showing conversation storage functionality.
"""
import sys
import os
from datetime import datetime
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.services.redis_client import RedisClient, get_redis_client, initialize_redis_client
    from backend.models.core import ConversationContext, Message
    print("✓ Successfully imported Redis client and models")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def create_sample_conversation() -> ConversationContext:
    """Create a sample conversation for demonstration."""
    messages = [
        Message(
            content="Hello! I need help with some calculations.",
            sender="user",
            timestamp=datetime.utcnow(),
            agent_type=None
        ),
        Message(
            content="I can help you with mathematical calculations. What would you like to calculate?",
            sender="agent",
            timestamp=datetime.utcnow(),
            agent_type="RouterAgent"
        ),
        Message(
            content="What is 65 * 3.11?",
            sender="user",
            timestamp=datetime.utcnow(),
            agent_type=None
        ),
        Message(
            content="65 * 3.11 = 202.15",
            sender="agent",
            timestamp=datetime.utcnow(),
            agent_type="MathAgent"
        )
    ]
    
    return ConversationContext(
        conversation_id="demo-conv-001",
        user_id="demo-user-123",
        timestamp=datetime.utcnow(),
        message_history=messages
    )


def demonstrate_redis_operations():
    """Demonstrate Redis client operations."""
    print("\nRedis Client Operations Demo")
    print("=" * 50)
    
    # Initialize Redis client
    print("\n1. Initializing Redis client...")
    client = RedisClient(host="localhost", port=6379, db=15)  # Use test database
    
    # Health check
    print("\n2. Performing health check...")
    if not client.health_check():
        print("✗ Redis is not available. Please start Redis server.")
        return False
    print("✓ Redis is healthy")
    
    # Create sample conversation
    print("\n3. Creating sample conversation...")
    conversation = create_sample_conversation()
    print(f"✓ Created conversation with {len(conversation.message_history)} messages")
    
    # Store conversation
    print("\n4. Storing conversation in Redis...")
    store_result = client.store_conversation(conversation, ttl=300)  # 5 minutes TTL
    if store_result:
        print("✓ Conversation stored successfully")
    else:
        print("✗ Failed to store conversation")
        return False
    
    # Retrieve conversation
    print("\n5. Retrieving conversation from Redis...")
    retrieved_conv = client.retrieve_conversation(conversation.conversation_id)
    if retrieved_conv:
        print(f"✓ Retrieved conversation with {len(retrieved_conv.message_history)} messages")
        print(f"  Conversation ID: {retrieved_conv.conversation_id}")
        print(f"  User ID: {retrieved_conv.user_id}")
        print(f"  Last message: {retrieved_conv.message_history[-1].content}")
    else:
        print("✗ Failed to retrieve conversation")
        return False
    
    # Add new message
    print("\n6. Adding new message to conversation...")
    new_message = Message(
        content="Thank you for the help!",
        sender="user",
        timestamp=datetime.utcnow(),
        agent_type=None
    )
    
    add_result = client.add_message_to_conversation(conversation.conversation_id, new_message)
    if add_result:
        print("✓ Message added successfully")
        
        # Verify message was added
        updated_conv = client.retrieve_conversation(conversation.conversation_id)
        if updated_conv and len(updated_conv.message_history) == 5:
            print(f"✓ Conversation now has {len(updated_conv.message_history)} messages")
        else:
            print("✗ Message count verification failed")
    else:
        print("✗ Failed to add message")
    
    # Get user conversations
    print("\n7. Getting user conversations...")
    user_conversations = client.get_user_conversations(conversation.user_id)
    if conversation.conversation_id in user_conversations:
        print(f"✓ Found {len(user_conversations)} conversations for user")
        print(f"  Conversations: {user_conversations}")
    else:
        print("✗ User conversations not found correctly")
    
    # TTL operations
    print("\n8. Testing TTL operations...")
    current_ttl = client.get_conversation_ttl(conversation.conversation_id)
    if current_ttl:
        print(f"✓ Current TTL: {current_ttl} seconds")
        
        # Set new TTL
        new_ttl = 600  # 10 minutes
        ttl_result = client.set_conversation_ttl(conversation.conversation_id, new_ttl)
        if ttl_result:
            print(f"✓ TTL updated to {new_ttl} seconds")
            
            # Verify new TTL
            updated_ttl = client.get_conversation_ttl(conversation.conversation_id)
            if updated_ttl and updated_ttl <= new_ttl:
                print(f"✓ TTL verification successful: {updated_ttl} seconds")
            else:
                print("✗ TTL verification failed")
        else:
            print("✗ Failed to update TTL")
    else:
        print("✗ Failed to get current TTL")
    
    # Create second conversation for the same user
    print("\n9. Creating second conversation for same user...")
    second_conv = ConversationContext(
        conversation_id="demo-conv-002",
        user_id="demo-user-123",  # Same user
        timestamp=datetime.utcnow(),
        message_history=[
            Message(
                content="I have another question about InfinitePay fees.",
                sender="user",
                timestamp=datetime.utcnow(),
                agent_type=None
            )
        ]
    )
    
    if client.store_conversation(second_conv):
        print("✓ Second conversation stored")
        
        # Verify user now has 2 conversations
        user_conversations = client.get_user_conversations(conversation.user_id)
        if len(user_conversations) == 2:
            print(f"✓ User now has {len(user_conversations)} conversations")
        else:
            print(f"✗ Expected 2 conversations, found {len(user_conversations)}")
    
    # Cleanup
    print("\n10. Cleaning up test data...")
    delete1 = client.delete_conversation(conversation.conversation_id, conversation.user_id)
    delete2 = client.delete_conversation(second_conv.conversation_id, second_conv.user_id)
    
    if delete1 and delete2:
        print("✓ Test conversations deleted successfully")
        
        # Verify cleanup
        final_conversations = client.get_user_conversations(conversation.user_id)
        if len(final_conversations) == 0:
            print("✓ Cleanup verification successful")
        else:
            print(f"✗ Cleanup verification failed: {len(final_conversations)} conversations remain")
    else:
        print("✗ Failed to delete test conversations")
    
    # Close connection
    print("\n11. Closing Redis connection...")
    client.close()
    print("✓ Connection closed")
    
    print("\n" + "=" * 50)
    print("✓ Redis operations demo completed successfully!")
    return True


def demonstrate_global_client():
    """Demonstrate global client functions."""
    print("\nGlobal Client Functions Demo")
    print("=" * 40)
    
    # Test get_redis_client
    print("\n1. Testing get_redis_client()...")
    client1 = get_redis_client()
    client2 = get_redis_client()
    
    if client1 is client2:
        print("✓ get_redis_client() returns same instance (singleton pattern)")
    else:
        print("✗ get_redis_client() should return same instance")
    
    # Test initialize_redis_client
    print("\n2. Testing initialize_redis_client()...")
    custom_client = initialize_redis_client(
        host="localhost",
        port=6379,
        db=14,  # Different database
        socket_timeout=10.0
    )
    
    if custom_client.host == "localhost" and custom_client.port == 6379 and custom_client.db == 14:
        print("✓ initialize_redis_client() created client with custom config")
    else:
        print("✗ initialize_redis_client() configuration failed")
    
    # Test that get_redis_client now returns the new instance
    client3 = get_redis_client()
    if client3 is custom_client:
        print("✓ get_redis_client() now returns the newly initialized client")
    else:
        print("✗ get_redis_client() should return the newly initialized client")
    
    print("\n" + "=" * 40)
    print("✓ Global client functions demo completed!")


def main():
    """Run the Redis demonstration."""
    print("Redis Client Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Run Redis operations demo
        if not demonstrate_redis_operations():
            print("\n✗ Redis operations demo failed")
            return False
        
        # Run global client demo
        demonstrate_global_client()
        
        print("\n" + "=" * 60)
        print("✓ All demonstrations completed successfully!")
        print("\nThis demo showed:")
        print("  • Redis client initialization and health checking")
        print("  • Conversation storage and retrieval")
        print("  • Message addition to existing conversations")
        print("  • User conversation management")
        print("  • TTL (Time To Live) operations")
        print("  • Multiple conversations per user")
        print("  • Conversation deletion and cleanup")
        print("  • Global client singleton pattern")
        print("  • Custom client initialization")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
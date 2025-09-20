"""
Unit tests for Redis client and conversation storage functionality.
"""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from backend.models.core import ConversationContext, Message
from backend.services.redis_client import RedisClient, get_redis_client, initialize_redis_client


class TestRedisClient:
    """Test cases for RedisClient class."""
    
    @pytest.fixture
    def mock_redis_pool(self):
        """Mock Redis connection pool."""
        with patch('services.redis_client.redis.ConnectionPool') as mock_pool:
            yield mock_pool
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        with patch('services.redis_client.redis.Redis') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def redis_client(self, mock_redis_pool, mock_redis_client):
        """Create RedisClient instance with mocked dependencies."""
        client = RedisClient(
            host="test-host",
            port=6380,
            db=1,
            password="test-password"
        )
        client.client = mock_redis_client
        return client
    
    @pytest.fixture
    def sample_conversation(self):
        """Create sample conversation for testing."""
        messages = [
            Message(
                content="Hello, how can I help?",
                sender="user",
                timestamp=datetime(2025, 1, 17, 10, 0, 0),
                agent_type=None
            ),
            Message(
                content="I can help you with math and knowledge questions.",
                sender="agent",
                timestamp=datetime(2025, 1, 17, 10, 0, 5),
                agent_type="RouterAgent"
            )
        ]
        
        return ConversationContext(
            conversation_id="test-conv-123",
            user_id="test-user-456",
            timestamp=datetime(2025, 1, 17, 10, 0, 0),
            message_history=messages
        )
    
    def test_redis_client_initialization(self, mock_redis_pool, mock_redis_client):
        """Test Redis client initialization with custom configuration."""
        client = RedisClient(
            host="custom-host",
            port=6380,
            db=2,
            password="custom-password",
            socket_timeout=10.0,
            max_connections=20
        )
        
        # Verify connection pool was created with correct parameters
        mock_redis_pool.assert_called_once_with(
            host="custom-host",
            port=6380,
            db=2,
            password="custom-password",
            socket_timeout=10.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=20
        )
        
        assert client.host == "custom-host"
        assert client.port == 6380
        assert client.db == 2
        assert client.password == "custom-password"
    
    def test_health_check_success(self, redis_client, mock_redis_client):
        """Test successful health check."""
        mock_redis_client.ping.return_value = True
        
        result = redis_client.health_check()
        
        assert result is True
        mock_redis_client.ping.assert_called_once()
    
    def test_health_check_failure_ping_false(self, redis_client, mock_redis_client):
        """Test health check failure when ping returns False."""
        mock_redis_client.ping.return_value = False
        
        result = redis_client.health_check()
        
        assert result is False
        mock_redis_client.ping.assert_called_once()
    
    def test_health_check_failure_exception(self, redis_client, mock_redis_client):
        """Test health check failure when exception is raised."""
        mock_redis_client.ping.side_effect = ConnectionError("Connection failed")
        
        result = redis_client.health_check()
        
        assert result is False
        mock_redis_client.ping.assert_called_once()
    
    def test_get_conversation_key(self, redis_client):
        """Test conversation key generation."""
        key = redis_client._get_conversation_key("test-conv-123")
        assert key == "conversation:test-conv-123"
    
    def test_get_user_conversations_key(self, redis_client):
        """Test user conversations key generation."""
        key = redis_client._get_user_conversations_key("test-user-456")
        assert key == "user_conversations:test-user-456"
    
    def test_store_conversation_success(self, redis_client, mock_redis_client, sample_conversation):
        """Test successful conversation storage."""
        # Mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [True, 1, True]  # All operations successful
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        result = redis_client.store_conversation(sample_conversation)
        
        assert result is True
        mock_redis_client.pipeline.assert_called_once()
        mock_pipeline.set.assert_called_once()
        mock_pipeline.sadd.assert_called_once()
        mock_pipeline.expire.assert_called_once()
        mock_pipeline.execute.assert_called_once()
    
    def test_store_conversation_with_custom_ttl(self, redis_client, mock_redis_client, sample_conversation):
        """Test conversation storage with custom TTL."""
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [True, 1, True]
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        custom_ttl = 3600  # 1 hour
        result = redis_client.store_conversation(sample_conversation, ttl=custom_ttl)
        
        assert result is True
        # Verify TTL was passed to set and expire calls
        mock_pipeline.set.assert_called_once()
        set_call_args = mock_pipeline.set.call_args
        assert set_call_args[1]['ex'] == custom_ttl
    
    def test_store_conversation_redis_error(self, redis_client, mock_redis_client, sample_conversation):
        """Test conversation storage with Redis error."""
        mock_redis_client.pipeline.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.store_conversation(sample_conversation)
        
        assert result is False
    
    def test_retrieve_conversation_success(self, redis_client, mock_redis_client, sample_conversation):
        """Test successful conversation retrieval."""
        # Prepare mock data
        conversation_data = {
            "conversation_id": "test-conv-123",
            "user_id": "test-user-456",
            "timestamp": "2025-01-17T10:00:00",
            "message_history": [
                {
                    "content": "Hello, how can I help?",
                    "sender": "user",
                    "timestamp": "2025-01-17T10:00:00",
                    "agent_type": None
                },
                {
                    "content": "I can help you with math and knowledge questions.",
                    "sender": "agent",
                    "timestamp": "2025-01-17T10:00:05",
                    "agent_type": "RouterAgent"
                }
            ],
            "created_at": "2025-01-17T10:00:00",
            "last_activity": "2025-01-17T10:00:05"
        }
        
        mock_redis_client.get.return_value = json.dumps(conversation_data)
        
        result = redis_client.retrieve_conversation("test-conv-123")
        
        assert result is not None
        assert result.conversation_id == "test-conv-123"
        assert result.user_id == "test-user-456"
        assert len(result.message_history) == 2
        assert result.message_history[0].content == "Hello, how can I help?"
        assert result.message_history[1].agent_type == "RouterAgent"
        
        mock_redis_client.get.assert_called_once_with("conversation:test-conv-123")
    
    def test_retrieve_conversation_not_found(self, redis_client, mock_redis_client):
        """Test conversation retrieval when conversation doesn't exist."""
        mock_redis_client.get.return_value = None
        
        result = redis_client.retrieve_conversation("non-existent-conv")
        
        assert result is None
        mock_redis_client.get.assert_called_once_with("conversation:non-existent-conv")
    
    def test_retrieve_conversation_json_error(self, redis_client, mock_redis_client):
        """Test conversation retrieval with invalid JSON."""
        mock_redis_client.get.return_value = "invalid json data"
        
        result = redis_client.retrieve_conversation("test-conv-123")
        
        assert result is None
    
    def test_retrieve_conversation_redis_error(self, redis_client, mock_redis_client):
        """Test conversation retrieval with Redis error."""
        mock_redis_client.get.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.retrieve_conversation("test-conv-123")
        
        assert result is None
    
    def test_add_message_to_conversation_success(self, redis_client, mock_redis_client, sample_conversation):
        """Test successfully adding message to existing conversation."""
        # Mock retrieve_conversation to return existing conversation
        with patch.object(redis_client, 'retrieve_conversation', return_value=sample_conversation):
            with patch.object(redis_client, 'store_conversation', return_value=True):
                new_message = Message(
                    content="What is 2 + 2?",
                    sender="user",
                    timestamp=datetime(2025, 1, 17, 10, 1, 0),
                    agent_type=None
                )
                
                result = redis_client.add_message_to_conversation("test-conv-123", new_message)
                
                assert result is True
    
    def test_add_message_to_nonexistent_conversation(self, redis_client, mock_redis_client):
        """Test adding message to non-existent conversation."""
        with patch.object(redis_client, 'retrieve_conversation', return_value=None):
            new_message = Message(
                content="What is 2 + 2?",
                sender="user",
                timestamp=datetime(2025, 1, 17, 10, 1, 0),
                agent_type=None
            )
            
            result = redis_client.add_message_to_conversation("non-existent-conv", new_message)
            
            assert result is False
    
    def test_get_user_conversations_success(self, redis_client, mock_redis_client):
        """Test successfully getting user conversations."""
        mock_redis_client.smembers.return_value = {"conv-1", "conv-2", "conv-3"}
        
        result = redis_client.get_user_conversations("test-user-456")
        
        assert len(result) == 3
        assert "conv-1" in result
        assert "conv-2" in result
        assert "conv-3" in result
        
        mock_redis_client.smembers.assert_called_once_with("user_conversations:test-user-456")
    
    def test_get_user_conversations_redis_error(self, redis_client, mock_redis_client):
        """Test getting user conversations with Redis error."""
        mock_redis_client.smembers.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.get_user_conversations("test-user-456")
        
        assert result == []
    
    def test_delete_conversation_success(self, redis_client, mock_redis_client):
        """Test successful conversation deletion."""
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [1, 1]  # Both operations successful
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        result = redis_client.delete_conversation("test-conv-123", "test-user-456")
        
        assert result is True
        mock_pipeline.delete.assert_called_once_with("conversation:test-conv-123")
        mock_pipeline.srem.assert_called_once_with("user_conversations:test-user-456", "test-conv-123")
    
    def test_delete_conversation_not_found(self, redis_client, mock_redis_client):
        """Test deleting non-existent conversation."""
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [0, 0]  # No keys deleted
        mock_redis_client.pipeline.return_value = mock_pipeline
        
        result = redis_client.delete_conversation("non-existent-conv", "test-user-456")
        
        assert result is False
    
    def test_delete_conversation_redis_error(self, redis_client, mock_redis_client):
        """Test conversation deletion with Redis error."""
        mock_redis_client.pipeline.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.delete_conversation("test-conv-123", "test-user-456")
        
        assert result is False
    
    def test_set_conversation_ttl_success(self, redis_client, mock_redis_client):
        """Test successfully setting conversation TTL."""
        mock_redis_client.expire.return_value = True
        
        result = redis_client.set_conversation_ttl("test-conv-123", 3600)
        
        assert result is True
        mock_redis_client.expire.assert_called_once_with("conversation:test-conv-123", 3600)
    
    def test_set_conversation_ttl_failure(self, redis_client, mock_redis_client):
        """Test setting TTL for non-existent conversation."""
        mock_redis_client.expire.return_value = False
        
        result = redis_client.set_conversation_ttl("non-existent-conv", 3600)
        
        assert result is False
    
    def test_set_conversation_ttl_redis_error(self, redis_client, mock_redis_client):
        """Test setting conversation TTL with Redis error."""
        mock_redis_client.expire.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.set_conversation_ttl("test-conv-123", 3600)
        
        assert result is False
    
    def test_get_conversation_ttl_success(self, redis_client, mock_redis_client):
        """Test successfully getting conversation TTL."""
        mock_redis_client.ttl.return_value = 3600
        
        result = redis_client.get_conversation_ttl("test-conv-123")
        
        assert result == 3600
        mock_redis_client.ttl.assert_called_once_with("conversation:test-conv-123")
    
    def test_get_conversation_ttl_not_found(self, redis_client, mock_redis_client):
        """Test getting TTL for non-existent conversation."""
        mock_redis_client.ttl.return_value = -2  # Key doesn't exist
        
        result = redis_client.get_conversation_ttl("non-existent-conv")
        
        assert result is None
    
    def test_get_conversation_ttl_no_ttl_set(self, redis_client, mock_redis_client):
        """Test getting TTL when no TTL is set."""
        mock_redis_client.ttl.return_value = -1  # Key exists but no TTL
        
        result = redis_client.get_conversation_ttl("test-conv-123")
        
        assert result is None
    
    def test_get_conversation_ttl_redis_error(self, redis_client, mock_redis_client):
        """Test getting conversation TTL with Redis error."""
        mock_redis_client.ttl.side_effect = ConnectionError("Redis connection failed")
        
        result = redis_client.get_conversation_ttl("test-conv-123")
        
        assert result is None
    
    def test_close_connection(self, redis_client):
        """Test closing Redis connection pool."""
        mock_pool = Mock()
        redis_client.pool = mock_pool
        
        redis_client.close()
        
        mock_pool.disconnect.assert_called_once()
    
    def test_close_connection_error(self, redis_client):
        """Test closing connection with error."""
        mock_pool = Mock()
        mock_pool.disconnect.side_effect = Exception("Disconnect error")
        redis_client.pool = mock_pool
        
        # Should not raise exception
        redis_client.close()
        
        mock_pool.disconnect.assert_called_once()


class TestRedisClientGlobalFunctions:
    """Test cases for global Redis client functions."""
    
    def test_get_redis_client_creates_instance(self):
        """Test that get_redis_client creates a new instance if none exists."""
        # Reset global client
        import services.redis_client
        services.redis_client.redis_client = None
        
        with patch('services.redis_client.RedisClient') as mock_redis_class:
            mock_instance = Mock()
            mock_redis_class.return_value = mock_instance
            
            result = get_redis_client()
            
            assert result == mock_instance
            mock_redis_class.assert_called_once()
    
    def test_get_redis_client_returns_existing_instance(self):
        """Test that get_redis_client returns existing instance."""
        # Set up existing instance
        import services.redis_client
        existing_instance = Mock()
        services.redis_client.redis_client = existing_instance
        
        result = get_redis_client()
        
        assert result == existing_instance
    
    def test_initialize_redis_client(self):
        """Test initializing Redis client with custom configuration."""
        with patch('services.redis_client.RedisClient') as mock_redis_class:
            mock_instance = Mock()
            mock_redis_class.return_value = mock_instance
            
            result = initialize_redis_client(
                host="custom-host",
                port=6380,
                db=2,
                password="custom-password",
                socket_timeout=10.0
            )
            
            assert result == mock_instance
            mock_redis_class.assert_called_once_with(
                host="custom-host",
                port=6380,
                db=2,
                password="custom-password",
                socket_timeout=10.0
            )


@pytest.mark.integration
class TestRedisClientIntegration:
    """Integration tests for Redis client (requires running Redis instance)."""
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis client for integration testing."""
        # Skip if Redis is not available
        try:
            client = RedisClient(host="localhost", port=6379, db=15)  # Use test database
            if not client.health_check():
                pytest.skip("Redis not available for integration tests")
            yield client
            # Cleanup
            client.client.flushdb()  # Clear test database
            client.close()
        except Exception:
            pytest.skip("Redis not available for integration tests")
    
    @pytest.fixture
    def sample_conversation(self):
        """Create sample conversation for integration testing."""
        messages = [
            Message(
                content="Hello, integration test!",
                sender="user",
                timestamp=datetime.utcnow(),
                agent_type=None
            )
        ]
        
        return ConversationContext(
            conversation_id="integration-test-conv",
            user_id="integration-test-user",
            timestamp=datetime.utcnow(),
            message_history=messages
        )
    
    def test_store_and_retrieve_conversation_integration(self, redis_client, sample_conversation):
        """Integration test for storing and retrieving conversation."""
        # Store conversation
        store_result = redis_client.store_conversation(sample_conversation)
        assert store_result is True
        
        # Retrieve conversation
        retrieved = redis_client.retrieve_conversation(sample_conversation.conversation_id)
        assert retrieved is not None
        assert retrieved.conversation_id == sample_conversation.conversation_id
        assert retrieved.user_id == sample_conversation.user_id
        assert len(retrieved.message_history) == 1
        assert retrieved.message_history[0].content == "Hello, integration test!"
    
    def test_add_message_integration(self, redis_client, sample_conversation):
        """Integration test for adding message to conversation."""
        # Store initial conversation
        redis_client.store_conversation(sample_conversation)
        
        # Add new message
        new_message = Message(
            content="This is a new message",
            sender="agent",
            timestamp=datetime.utcnow(),
            agent_type="TestAgent"
        )
        
        add_result = redis_client.add_message_to_conversation(
            sample_conversation.conversation_id, 
            new_message
        )
        assert add_result is True
        
        # Verify message was added
        retrieved = redis_client.retrieve_conversation(sample_conversation.conversation_id)
        assert len(retrieved.message_history) == 2
        assert retrieved.message_history[1].content == "This is a new message"
        assert retrieved.message_history[1].agent_type == "TestAgent"
    
    def test_user_conversations_integration(self, redis_client, sample_conversation):
        """Integration test for user conversation management."""
        # Store conversation
        redis_client.store_conversation(sample_conversation)
        
        # Get user conversations
        conversations = redis_client.get_user_conversations(sample_conversation.user_id)
        assert sample_conversation.conversation_id in conversations
        
        # Delete conversation
        delete_result = redis_client.delete_conversation(
            sample_conversation.conversation_id,
            sample_conversation.user_id
        )
        assert delete_result is True
        
        # Verify conversation is deleted
        retrieved = redis_client.retrieve_conversation(sample_conversation.conversation_id)
        assert retrieved is None
        
        # Verify conversation removed from user list
        conversations = redis_client.get_user_conversations(sample_conversation.user_id)
        assert sample_conversation.conversation_id not in conversations
    
    def test_ttl_integration(self, redis_client, sample_conversation):
        """Integration test for TTL functionality."""
        # Store conversation with short TTL
        short_ttl = 5  # 5 seconds
        redis_client.store_conversation(sample_conversation, ttl=short_ttl)
        
        # Check TTL is set
        ttl = redis_client.get_conversation_ttl(sample_conversation.conversation_id)
        assert ttl is not None
        assert ttl <= short_ttl
        assert ttl > 0
        
        # Update TTL
        new_ttl = 10
        set_result = redis_client.set_conversation_ttl(sample_conversation.conversation_id, new_ttl)
        assert set_result is True
        
        # Verify new TTL
        updated_ttl = redis_client.get_conversation_ttl(sample_conversation.conversation_id)
        assert updated_ttl is not None
        assert updated_ttl <= new_ttl
        assert updated_ttl > short_ttl
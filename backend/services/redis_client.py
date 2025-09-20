"""
Redis client configuration and conversation storage functionality.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from models.core import ConversationContext, Message

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for conversation storage and management."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        max_connections: int = 10,
    ):
        """
        Initialize Redis client with connection configuration.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Health check interval in seconds
            max_connections: Maximum number of connections in pool
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # Connection pool configuration
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            health_check_interval=health_check_interval,
            max_connections=max_connections,
        )
        
        # Redis client instance
        self.client = redis.Redis(connection_pool=self.pool, decode_responses=True)
        
        # Default TTL for conversations (7 days)
        self.default_conversation_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
        
        logger.info(f"Redis client initialized for {host}:{port}")
    
    def health_check(self) -> bool:
        """
        Perform health check on Redis connection.
        
        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        try:
            response = self.client.ping()
            if response:
                logger.debug("Redis health check passed")
                return True
            else:
                logger.warning("Redis health check failed: ping returned False")
                return False
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def _get_conversation_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation storage."""
        return f"conversation:{conversation_id}"
    
    def _get_user_conversations_key(self, user_id: str) -> str:
        """Generate Redis key for user's conversation list."""
        return f"user_conversations:{user_id}"
    
    def store_conversation(
        self, 
        conversation: ConversationContext, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store conversation context in Redis.
        
        Args:
            conversation: ConversationContext to store
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            conversation_key = self._get_conversation_key(conversation.conversation_id)
            user_conversations_key = self._get_user_conversations_key(conversation.user_id)
            
            # Serialize conversation to JSON
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
            
            # Use pipeline for atomic operations
            pipe = self.client.pipeline()
            
            # Store conversation data
            pipe.set(
                conversation_key,
                json.dumps(conversation_data),
                ex=ttl or self.default_conversation_ttl
            )
            
            # Add conversation to user's conversation list
            pipe.sadd(user_conversations_key, conversation.conversation_id)
            pipe.expire(user_conversations_key, ttl or self.default_conversation_ttl)
            
            # Execute pipeline
            results = pipe.execute()
            
            if all(results):
                logger.info(f"Stored conversation {conversation.conversation_id} for user {conversation.user_id}")
                return True
            else:
                logger.error(f"Failed to store conversation {conversation.conversation_id}")
                return False
                
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error storing conversation {conversation.conversation_id}: {e}")
            return False
        except (json.JSONEncodeError, Exception) as e:
            logger.error(f"Error serializing conversation {conversation.conversation_id}: {e}")
            return False
    
    def retrieve_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context from Redis.
        
        Args:
            conversation_id: ID of conversation to retrieve
            
        Returns:
            ConversationContext if found, None otherwise
        """
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            conversation_data = self.client.get(conversation_key)
            
            if not conversation_data:
                logger.debug(f"Conversation {conversation_id} not found in Redis")
                return None
            
            # Deserialize conversation from JSON
            data = json.loads(conversation_data)
            
            # Parse message history
            messages = []
            for msg_data in data.get("message_history", []):
                message = Message(
                    content=msg_data["content"],
                    sender=msg_data["sender"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    agent_type=msg_data.get("agent_type"),
                )
                messages.append(message)
            
            # Create ConversationContext
            conversation = ConversationContext(
                conversation_id=data["conversation_id"],
                user_id=data["user_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                message_history=messages,
            )
            
            logger.debug(f"Retrieved conversation {conversation_id} with {len(messages)} messages")
            return conversation
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error retrieving conversation {conversation_id}: {e}")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error deserializing conversation {conversation_id}: {e}")
            return None
    
    def add_message_to_conversation(
        self, 
        conversation_id: str, 
        message: Message,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Add a message to an existing conversation.
        
        Args:
            conversation_id: ID of conversation to update
            message: Message to add
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            bool: True if message added successfully, False otherwise
        """
        try:
            # Retrieve existing conversation
            conversation = self.retrieve_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Cannot add message to non-existent conversation {conversation_id}")
                return False
            
            # Add new message
            conversation.message_history.append(message)
            
            # Store updated conversation
            return self.store_conversation(conversation, ttl)
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            return False
    
    def get_user_conversations(self, user_id: str) -> list[str]:
        """
        Get list of conversation IDs for a user.
        
        Args:
            user_id: User ID to get conversations for
            
        Returns:
            List of conversation IDs
        """
        try:
            user_conversations_key = self._get_user_conversations_key(user_id)
            conversation_ids = self.client.smembers(user_conversations_key)
            
            logger.debug(f"Found {len(conversation_ids)} conversations for user {user_id}")
            return list(conversation_ids)
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error getting conversations for user {user_id}: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation from Redis.
        
        Args:
            conversation_id: ID of conversation to delete
            user_id: User ID (for removing from user's conversation list)
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            user_conversations_key = self._get_user_conversations_key(user_id)
            
            # Use pipeline for atomic operations
            pipe = self.client.pipeline()
            pipe.delete(conversation_key)
            pipe.srem(user_conversations_key, conversation_id)
            
            results = pipe.execute()
            
            if results[0] > 0:  # At least one key was deleted
                logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
                return True
            else:
                logger.warning(f"Conversation {conversation_id} not found for deletion")
                return False
                
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error deleting conversation {conversation_id}: {e}")
            return False
    
    def set_conversation_ttl(self, conversation_id: str, ttl: int) -> bool:
        """
        Set TTL for a conversation.
        
        Args:
            conversation_id: ID of conversation
            ttl: Time to live in seconds
            
        Returns:
            bool: True if TTL set successfully, False otherwise
        """
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            result = self.client.expire(conversation_key, ttl)
            
            if result:
                logger.debug(f"Set TTL {ttl}s for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"Failed to set TTL for conversation {conversation_id}")
                return False
                
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error setting TTL for conversation {conversation_id}: {e}")
            return False
    
    def get_conversation_ttl(self, conversation_id: str) -> Optional[int]:
        """
        Get remaining TTL for a conversation.
        
        Args:
            conversation_id: ID of conversation
            
        Returns:
            Remaining TTL in seconds, None if not found or no TTL set
        """
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            ttl = self.client.ttl(conversation_key)
            
            if ttl == -2:  # Key doesn't exist
                logger.debug(f"Conversation {conversation_id} not found")
                return None
            elif ttl == -1:  # Key exists but no TTL set
                logger.debug(f"Conversation {conversation_id} has no TTL")
                return None
            else:
                return ttl
                
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Redis error getting TTL for conversation {conversation_id}: {e}")
            return None
    
    def close(self) -> None:
        """Close Redis connection pool."""
        try:
            self.pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")


# Global Redis client instance
redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance.
    
    Returns:
        RedisClient instance
    """
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
    return redis_client


def initialize_redis_client(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    **kwargs
) -> RedisClient:
    """
    Initialize global Redis client with custom configuration.
    
    Args:
        host: Redis server host
        port: Redis server port
        db: Redis database number
        password: Redis password (if required)
        **kwargs: Additional Redis configuration options
        
    Returns:
        RedisClient instance
    """
    global redis_client
    redis_client = RedisClient(
        host=host,
        port=port,
        db=db,
        password=password,
        **kwargs
    )
    return redis_client
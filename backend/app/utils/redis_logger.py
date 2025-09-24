"""
Redis-based simplified logging system for the modular chatbot.
Provides structured logging with Redis storage for log entries.
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from services.redis_client import get_redis_client


class LogLevel(Enum):
    """Log levels for Redis logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RedisLogger:
    """Redis-based logger for structured logging."""
    
    def __init__(self, redis_client=None, max_logs_per_key: int = 1000, log_ttl: int = 7 * 24 * 60 * 60):
        """
        Initialize Redis logger.
        
        Args:
            redis_client: Redis client instance (uses global if None)
            max_logs_per_key: Maximum number of logs to keep per key
            log_ttl: Time to live for log entries in seconds (default: 7 days)
        """
        self.redis_client = redis_client or get_redis_client()
        self.max_logs_per_key = max_logs_per_key
        self.log_ttl = log_ttl
    
    def _get_log_key(self, level: LogLevel, component: str = "general") -> str:
        """Generate Redis key for log entries."""
        return f"logs:{component}:{level.value.lower()}"
    
    def _get_log_entry(self, message: str, level: LogLevel, component: str, 
                      extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create structured log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "component": component,
            "message": message,
            "extra": extra or {}
        }
        return log_entry
    
    def _store_log(self, log_entry: Dict[str, Any], level: LogLevel, component: str) -> bool:
        """Store log entry in Redis."""
        try:
            log_key = self._get_log_key(level, component)
            log_data = json.dumps(log_entry)
            
            # Use Redis list to store logs (LPUSH for recent-first ordering)
            self.redis_client.client.lpush(log_key, log_data)
            
            # Set TTL for the log key
            self.redis_client.client.expire(log_key, self.log_ttl)
            
            # Trim list to max_logs_per_key to prevent memory issues
            self.redis_client.client.ltrim(log_key, 0, self.max_logs_per_key - 1)
            
            return True
        except Exception as e:
            # Fallback to console logging if Redis fails
            print(f"Redis logging failed: {e}")
            print(f"Log entry: {log_entry}")
            return False
    
    def debug(self, message: str, component: str = "general", extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        log_entry = self._get_log_entry(message, LogLevel.DEBUG, component, extra)
        self._store_log(log_entry, LogLevel.DEBUG, component)
    
    def info(self, message: str, component: str = "general", extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        log_entry = self._get_log_entry(message, LogLevel.INFO, component, extra)
        self._store_log(log_entry, LogLevel.INFO, component)
    
    def warning(self, message: str, component: str = "general", extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        log_entry = self._get_log_entry(message, LogLevel.WARNING, component, extra)
        self._store_log(log_entry, LogLevel.WARNING, component)
    
    def error(self, message: str, component: str = "general", extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        log_entry = self._get_log_entry(message, LogLevel.ERROR, component, extra)
        self._store_log(log_entry, LogLevel.ERROR, component)
    
    def critical(self, message: str, component: str = "general", extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        log_entry = self._get_log_entry(message, LogLevel.CRITICAL, component, extra)
        self._store_log(log_entry, LogLevel.CRITICAL, component)
    
    def get_logs(self, level: LogLevel, component: str = "general", 
                limit: int = 100, start: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve logs from Redis.
        
        Args:
            level: Log level to retrieve
            component: Component to retrieve logs for
            limit: Maximum number of logs to retrieve
            start: Starting index (for pagination)
            
        Returns:
            List of log entries
        """
        try:
            log_key = self._get_log_key(level, component)
            
            # Get logs from Redis list
            logs_data = self.redis_client.client.lrange(log_key, start, start + limit - 1)
            
            logs = []
            for log_data in logs_data:
                try:
                    log_entry = json.loads(log_data)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
            
            return logs
        except Exception as e:
            print(f"Failed to retrieve logs: {e}")
            return []
    
    def get_recent_logs(self, component: str = "general", hours: int = 24, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent logs across all levels for a component.
        
        Args:
            component: Component to get logs for
            hours: Number of hours to look back
            limit: Maximum number of logs to return
            
        Returns:
            List of recent log entries
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            all_logs = []
            
            # Get logs from all levels
            for level in LogLevel:
                logs = self.get_logs(level, component, limit=limit)
                all_logs.extend(logs)
            
            # Filter by timestamp and sort
            recent_logs = []
            for log in all_logs:
                try:
                    log_time = datetime.fromisoformat(log["timestamp"])
                    if log_time >= cutoff_time:
                        recent_logs.append(log)
                except (KeyError, ValueError):
                    continue
            
            # Sort by timestamp (most recent first)
            recent_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return recent_logs[:limit]
        except Exception as e:
            print(f"Failed to get recent logs: {e}")
            return []
    
    def clear_logs(self, level: Optional[LogLevel] = None, component: str = "general") -> bool:
        """
        Clear logs from Redis.
        
        Args:
            level: Log level to clear (None for all levels)
            component: Component to clear logs for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if level:
                log_key = self._get_log_key(level, component)
                self.redis_client.client.delete(log_key)
            else:
                # Clear all levels for component
                for log_level in LogLevel:
                    log_key = self._get_log_key(log_level, component)
                    self.redis_client.client.delete(log_key)
            
            return True
        except Exception as e:
            print(f"Failed to clear logs: {e}")
            return False
    
    def get_log_stats(self, component: str = "general") -> Dict[str, Any]:
        """
        Get logging statistics for a component.
        
        Args:
            component: Component to get stats for
            
        Returns:
            Dictionary with log statistics
        """
        try:
            stats = {
                "component": component,
                "timestamp": datetime.utcnow().isoformat(),
                "levels": {}
            }
            
            for level in LogLevel:
                log_key = self._get_log_key(level, component)
                count = self.redis_client.client.llen(log_key)
                stats["levels"][level.value.lower()] = count
            
            stats["total"] = sum(stats["levels"].values())
            
            return stats
        except Exception as e:
            print(f"Failed to get log stats: {e}")
            return {"error": str(e)}


# Global Redis logger instance
_redis_logger: Optional[RedisLogger] = None


def get_redis_logger() -> RedisLogger:
    """Get global Redis logger instance."""
    global _redis_logger
    if _redis_logger is None:
        _redis_logger = RedisLogger()
    return _redis_logger


def initialize_redis_logger(redis_client=None, **kwargs) -> RedisLogger:
    """Initialize global Redis logger with custom configuration."""
    global _redis_logger
    _redis_logger = RedisLogger(redis_client=redis_client, **kwargs)
    return _redis_logger


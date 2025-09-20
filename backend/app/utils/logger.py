"""
Structured logging system for the modular chatbot.

This module provides structured JSON logging with consistent formatting
across all agents and system components.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextlib import contextmanager
from functools import wraps


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure with required fields
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add optional fields if present in record
        optional_fields = [
            "agent", "conversation_id", "user_id", "execution_time",
            "decision", "confidence", "metadata", "error_details"
        ]
        
        for field in optional_fields:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_entry[field] = getattr(record, field)
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ChatbotLogger:
    """Main logger class for the chatbot system."""
    
    def __init__(self, name: str = "chatbot"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the logger with structured formatting."""
        if not self.logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            
            # Set log level based on environment (default to INFO)
            self.logger.setLevel(logging.INFO)
            self.logger.addHandler(handler)
            
            # Prevent duplicate logs
            self.logger.propagate = False
    
    def log(
        self,
        level: str,
        message: str,
        agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        execution_time: Optional[float] = None,
        decision: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None,
        **kwargs
    ):
        """Log a structured message with optional fields."""
        # Create extra dict with non-None values
        extra = {}
        if agent is not None:
            extra["agent"] = agent
        if conversation_id is not None:
            extra["conversation_id"] = conversation_id
        if user_id is not None:
            extra["user_id"] = user_id
        if execution_time is not None:
            extra["execution_time"] = execution_time
        if decision is not None:
            extra["decision"] = decision
        if confidence is not None:
            extra["confidence"] = confidence
        if metadata is not None:
            extra["metadata"] = metadata
        if error_details is not None:
            extra["error_details"] = error_details
        
        # Handle additional kwargs, especially 'extra' from standard logging
        if 'extra' in kwargs:
            extra.update(kwargs['extra'])
        
        # Handle other standard logging kwargs
        for key in ['exc_info', 'stack_info', 'stacklevel']:
            if key in kwargs:
                # These will be passed directly to the logging call
                pass
        
        # Log with appropriate level
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Prepare logging kwargs
        log_kwargs = {'extra': extra}
        for key in ['exc_info', 'stack_info', 'stacklevel']:
            if key in kwargs:
                log_kwargs[key] = kwargs[key]
        
        self.logger.log(log_level, message, **log_kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self.log("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.log("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self.log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self.log("CRITICAL", message, **kwargs)


class AgentLogger:
    """Specialized logger for agent operations."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = ChatbotLogger(f"agent.{agent_name.lower()}")
    
    def log_decision(
        self,
        message: str,
        decision: str,
        confidence: float,
        conversation_id: str,
        user_id: str,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an agent decision with all required fields."""
        self.logger.info(
            message,
            agent=self.agent_name,
            conversation_id=conversation_id,
            user_id=user_id,
            execution_time=execution_time,
            decision=decision,
            confidence=confidence,
            metadata=metadata,
        )
    
    def log_processing(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log agent processing details."""
        self.logger.info(
            message,
            agent=self.agent_name,
            conversation_id=conversation_id,
            user_id=user_id,
            execution_time=execution_time,
            metadata=metadata,
        )
    
    def log_error(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        error_details: str,
        execution_time: Optional[float] = None,
    ):
        """Log agent errors."""
        self.logger.error(
            message,
            agent=self.agent_name,
            conversation_id=conversation_id,
            user_id=user_id,
            execution_time=execution_time,
            error_details=error_details,
        )


@contextmanager
def performance_timer():
    """Context manager to measure execution time."""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        # Store execution time in context for later use
        performance_timer.last_execution_time = execution_time


def log_performance(agent_name: str):
    """Decorator to log function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = AgentLogger(agent_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Extract context from function arguments if available
                conversation_id = kwargs.get("conversation_id", "unknown")
                user_id = kwargs.get("user_id", "unknown")
                
                logger.log_processing(
                    f"Function {func.__name__} completed successfully",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    execution_time=execution_time,
                    metadata={"function": func.__name__},
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                conversation_id = kwargs.get("conversation_id", "unknown")
                user_id = kwargs.get("user_id", "unknown")
                
                logger.log_error(
                    f"Function {func.__name__} failed",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    error_details=str(e),
                    execution_time=execution_time,
                )
                raise
        
        return wrapper
    return decorator


# Global logger instances for different components
main_logger = ChatbotLogger("main")
router_logger = AgentLogger("RouterAgent")
math_logger = AgentLogger("MathAgent")
knowledge_logger = AgentLogger("KnowledgeAgent")
api_logger = ChatbotLogger("api")


def configure_logging(level: str = "INFO", format_type: str = "json"):
    """Configure global logging settings."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Update all chatbot loggers
    for logger_name in ["main", "api", "agent.routeragent", "agent.mathagent", "agent.knowledgeagent"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)


def get_logger(name: str) -> ChatbotLogger:
    """Get a logger instance for a specific component."""
    return ChatbotLogger(name)


def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get an agent logger instance."""
    return AgentLogger(agent_name)
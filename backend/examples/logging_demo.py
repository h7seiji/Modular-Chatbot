"""
Demonstration of the structured logging system.

This script shows how to use the logging utilities for different
agent types and system components.
"""

import time
from app.utils.logger import (
    AgentLogger,
    ChatbotLogger,
    log_performance,
    performance_timer,
    router_logger,
    math_logger,
    knowledge_logger,
    api_logger,
)
from app.utils.logging_config import initialize_logging


def demo_basic_logging():
    """Demonstrate basic logging functionality."""
    print("=== Basic Logging Demo ===")
    
    # Initialize logging
    initialize_logging()
    
    # Create a custom logger
    custom_logger = ChatbotLogger("demo")
    
    # Log different levels
    custom_logger.info("Application started")
    custom_logger.debug("Debug information", metadata={"debug_key": "debug_value"})
    custom_logger.warning("This is a warning")
    custom_logger.error("An error occurred", error_details="Sample error details")


def demo_agent_logging():
    """Demonstrate agent-specific logging."""
    print("\n=== Agent Logging Demo ===")
    
    # Router Agent logging
    router_logger.log_decision(
        message="Routing user query to appropriate agent",
        decision="KnowledgeAgent",
        confidence=0.92,
        conversation_id="conv-demo-001",
        user_id="user-demo-123",
        execution_time=0.045,
        metadata={
            "query_type": "knowledge",
            "alternatives": ["MathAgent"],
            "input_tokens": 25,
        }
    )
    
    # Math Agent logging
    math_logger.log_processing(
        message="Processing mathematical expression",
        conversation_id="conv-demo-002",
        user_id="user-demo-456",
        execution_time=0.123,
        metadata={
            "expression": "2 + 2 * 3",
            "result": 8,
            "complexity": "simple",
        }
    )
    
    # Knowledge Agent logging
    knowledge_logger.log_processing(
        message="Retrieving knowledge from vector database",
        conversation_id="conv-demo-003",
        user_id="user-demo-789",
        execution_time=0.234,
        metadata={
            "query": "What is machine learning?",
            "sources_found": 5,
            "relevance_score": 0.87,
        }
    )


def demo_error_logging():
    """Demonstrate error logging."""
    print("\n=== Error Logging Demo ===")
    
    # Agent error
    router_logger.log_error(
        message="Failed to route user query",
        conversation_id="conv-error-001",
        user_id="user-error-123",
        error_details="No suitable agent found for query type",
        execution_time=0.012,
    )
    
    # API error
    api_logger.error(
        "API request failed",
        conversation_id="conv-error-002",
        user_id="user-error-456",
        error_details="External service timeout",
        metadata={
            "endpoint": "/api/external",
            "status_code": 504,
            "retry_count": 3,
        }
    )


def demo_performance_timing():
    """Demonstrate performance timing."""
    print("\n=== Performance Timing Demo ===")
    
    # Using context manager
    with performance_timer():
        time.sleep(0.1)  # Simulate work
        print(f"Operation took: {performance_timer.last_execution_time:.3f} seconds")
    
    # Using decorator
    @log_performance("DemoAgent")
    def slow_operation(conversation_id="conv-perf-001", user_id="user-perf-123"):
        """Simulate a slow operation."""
        time.sleep(0.05)
        return "Operation completed"
    
    result = slow_operation()
    print(f"Decorated function result: {result}")


def demo_custom_agent_logger():
    """Demonstrate creating custom agent loggers."""
    print("\n=== Custom Agent Logger Demo ===")
    
    # Create custom agent logger
    custom_agent = AgentLogger("CustomAgent")
    
    # Log various operations
    custom_agent.log_decision(
        message="Custom agent making a decision",
        decision="ProcessWithCustomLogic",
        confidence=0.78,
        conversation_id="conv-custom-001",
        user_id="user-custom-123",
        execution_time=0.089,
        metadata={
            "custom_field": "custom_value",
            "processing_mode": "advanced",
        }
    )
    
    custom_agent.log_processing(
        message="Custom processing completed",
        conversation_id="conv-custom-001",
        user_id="user-custom-123",
        execution_time=0.156,
        metadata={
            "items_processed": 42,
            "success_rate": 0.95,
        }
    )


def demo_structured_metadata():
    """Demonstrate structured metadata logging."""
    print("\n=== Structured Metadata Demo ===")
    
    logger = ChatbotLogger("metadata_demo")
    
    # Complex metadata structure
    complex_metadata = {
        "request": {
            "method": "POST",
            "endpoint": "/api/chat",
            "headers": {
                "content-type": "application/json",
                "user-agent": "ChatbotClient/1.0",
            }
        },
        "processing": {
            "steps": ["validation", "routing", "execution", "response"],
            "timing": {
                "validation": 0.005,
                "routing": 0.012,
                "execution": 0.234,
                "response": 0.008,
            }
        },
        "result": {
            "success": True,
            "tokens_used": 150,
            "confidence": 0.89,
        }
    }
    
    logger.info(
        "Request processed successfully",
        agent="RouterAgent",
        conversation_id="conv-meta-001",
        user_id="user-meta-123",
        execution_time=0.259,
        metadata=complex_metadata,
    )


def main():
    """Run all logging demonstrations."""
    print("Structured Logging System Demonstration")
    print("=" * 50)
    
    demo_basic_logging()
    demo_agent_logging()
    demo_error_logging()
    demo_performance_timing()
    demo_custom_agent_logger()
    demo_structured_metadata()
    
    print("\n" + "=" * 50)
    print("Demo completed! Check the console output above for JSON logs.")
    print("In a real application, these logs would be captured by your")
    print("log aggregation system (e.g., ELK stack, Fluentd, etc.)")


if __name__ == "__main__":
    main()
"""
Tests for the structured logging system.
"""

import json
import logging
import time
from io import StringIO
from unittest.mock import patch

import pytest

from app.utils.logger import (
    AgentLogger,
    ChatbotLogger,
    StructuredFormatter,
    configure_logging,
    get_agent_logger,
    get_logger,
    log_performance,
    performance_timer,
)


class TestStructuredFormatter:
    """Test the structured JSON formatter."""
    
    def test_basic_formatting(self):
        """Test basic log formatting with required fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
    
    def test_optional_fields(self):
        """Test formatting with optional fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        # Add optional fields
        record.agent = "TestAgent"
        record.conversation_id = "conv-123"
        record.user_id = "user-456"
        record.execution_time = 0.045
        record.decision = "TestDecision"
        record.confidence = 0.92
        record.metadata = {"key": "value"}
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["agent"] == "TestAgent"
        assert log_data["conversation_id"] == "conv-123"
        assert log_data["user_id"] == "user-456"
        assert log_data["execution_time"] == 0.045
        assert log_data["decision"] == "TestDecision"
        assert log_data["confidence"] == 0.92
        assert log_data["metadata"] == {"key": "value"}
    
    def test_exception_formatting(self):
        """Test formatting with exception information."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=True,
            )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]


class TestChatbotLogger:
    """Test the main chatbot logger."""
    
    def setup_method(self):
        """Set up test logger with string capture."""
        self.log_capture = StringIO()
        self.logger = ChatbotLogger("test")
        
        # Replace handler with string capture
        self.logger.logger.handlers.clear()
        handler = logging.StreamHandler(self.log_capture)
        handler.setFormatter(StructuredFormatter())
        self.logger.logger.addHandler(handler)
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        self.logger.info("Test message")
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
    
    def test_logging_with_all_fields(self):
        """Test logging with all optional fields."""
        self.logger.info(
            "Test message",
            agent="TestAgent",
            conversation_id="conv-123",
            user_id="user-456",
            execution_time=0.045,
            decision="TestDecision",
            confidence=0.92,
            metadata={"key": "value"},
        )
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["agent"] == "TestAgent"
        assert log_data["conversation_id"] == "conv-123"
        assert log_data["user_id"] == "user-456"
        assert log_data["execution_time"] == 0.045
        assert log_data["decision"] == "TestDecision"
        assert log_data["confidence"] == 0.92
        assert log_data["metadata"] == {"key": "value"}
    
    def test_different_log_levels(self):
        """Test different log levels."""
        test_cases = [
            ("debug", "DEBUG"),
            ("info", "INFO"),
            ("warning", "WARNING"),
            ("error", "ERROR"),
            ("critical", "CRITICAL"),
        ]
        
        for method_name, expected_level in test_cases:
            self.log_capture.truncate(0)
            self.log_capture.seek(0)
            
            method = getattr(self.logger, method_name)
            method("Test message")
            
            log_output = self.log_capture.getvalue()
            if log_output.strip():  # Some levels might be filtered
                log_data = json.loads(log_output.strip())
                assert log_data["level"] == expected_level
    
    def test_error_logging_with_details(self):
        """Test error logging with error details."""
        self.logger.error(
            "An error occurred",
            agent="TestAgent",
            conversation_id="conv-123",
            user_id="user-456",
            error_details="Detailed error information",
        )
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["level"] == "ERROR"
        assert log_data["error_details"] == "Detailed error information"


class TestAgentLogger:
    """Test the agent-specific logger."""
    
    def setup_method(self):
        """Set up test agent logger with string capture."""
        self.log_capture = StringIO()
        self.agent_logger = AgentLogger("TestAgent")
        
        # Replace handler with string capture
        self.agent_logger.logger.logger.handlers.clear()
        handler = logging.StreamHandler(self.log_capture)
        handler.setFormatter(StructuredFormatter())
        self.agent_logger.logger.logger.addHandler(handler)
    
    def test_log_decision(self):
        """Test logging agent decisions."""
        self.agent_logger.log_decision(
            message="Routing decision made",
            decision="KnowledgeAgent",
            confidence=0.92,
            conversation_id="conv-123",
            user_id="user-456",
            execution_time=0.045,
            metadata={"query_type": "knowledge"},
        )
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["agent"] == "TestAgent"
        assert log_data["decision"] == "KnowledgeAgent"
        assert log_data["confidence"] == 0.92
        assert log_data["conversation_id"] == "conv-123"
        assert log_data["user_id"] == "user-456"
        assert log_data["execution_time"] == 0.045
        assert log_data["metadata"]["query_type"] == "knowledge"
    
    def test_log_processing(self):
        """Test logging agent processing details."""
        self.agent_logger.log_processing(
            message="Processing query",
            conversation_id="conv-123",
            user_id="user-456",
            execution_time=0.123,
            metadata={"processed_tokens": 150},
        )
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["agent"] == "TestAgent"
        assert log_data["message"] == "Processing query"
        assert log_data["execution_time"] == 0.123
        assert log_data["metadata"]["processed_tokens"] == 150
    
    def test_log_error(self):
        """Test logging agent errors."""
        self.agent_logger.log_error(
            message="Agent processing failed",
            conversation_id="conv-123",
            user_id="user-456",
            error_details="Connection timeout",
            execution_time=5.0,
        )
        
        log_output = self.log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["level"] == "ERROR"
        assert log_data["agent"] == "TestAgent"
        assert log_data["error_details"] == "Connection timeout"
        assert log_data["execution_time"] == 5.0


class TestPerformanceTimer:
    """Test the performance timing context manager."""
    
    def test_performance_timer(self):
        """Test performance timing functionality."""
        with performance_timer():
            time.sleep(0.01)  # Small delay for testing
        
        # Check that execution time was recorded
        assert hasattr(performance_timer, "last_execution_time")
        assert performance_timer.last_execution_time >= 0.01
        assert performance_timer.last_execution_time < 0.1  # Should be quick


class TestLogPerformanceDecorator:
    """Test the performance logging decorator."""
    
    def setup_method(self):
        """Set up test with log capture."""
        self.log_capture = StringIO()
        
        # Patch the agent logger to capture output
        self.original_handler = None
    
    def test_successful_function_logging(self):
        """Test logging for successful function execution."""
        @log_performance("TestAgent")
        def test_function(conversation_id="conv-123", user_id="user-456"):
            return "success"
        
        with patch("app.utils.logger.AgentLogger") as mock_agent_logger:
            mock_logger_instance = mock_agent_logger.return_value
            
            result = test_function()
            
            assert result == "success"
            mock_agent_logger.assert_called_once_with("TestAgent")
            mock_logger_instance.log_processing.assert_called_once()
            
            # Check the call arguments
            call_args = mock_logger_instance.log_processing.call_args
            assert "Function test_function completed successfully" in call_args[0][0]
            assert call_args[1]["conversation_id"] == "conv-123"
            assert call_args[1]["user_id"] == "user-456"
            assert "execution_time" in call_args[1]
    
    def test_failed_function_logging(self):
        """Test logging for failed function execution."""
        @log_performance("TestAgent")
        def failing_function(conversation_id="conv-123", user_id="user-456"):
            raise ValueError("Test error")
        
        with patch("app.utils.logger.AgentLogger") as mock_agent_logger:
            mock_logger_instance = mock_agent_logger.return_value
            
            with pytest.raises(ValueError):
                failing_function()
            
            mock_agent_logger.assert_called_once_with("TestAgent")
            mock_logger_instance.log_error.assert_called_once()
            
            # Check the call arguments
            call_args = mock_logger_instance.log_error.call_args
            assert "Function failing_function failed" in call_args[0][0]
            assert call_args[1]["error_details"] == "Test error"


class TestLoggerConfiguration:
    """Test logger configuration functions."""
    
    def test_configure_logging(self):
        """Test global logging configuration."""
        configure_logging(level="DEBUG", format_type="json")
        
        # Check that root logger level was set
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_component")
        assert isinstance(logger, ChatbotLogger)
        assert logger.logger.name == "test_component"
    
    def test_get_agent_logger(self):
        """Test getting an agent logger instance."""
        agent_logger = get_agent_logger("TestAgent")
        assert isinstance(agent_logger, AgentLogger)
        assert agent_logger.agent_name == "TestAgent"


class TestLoggerIntegration:
    """Integration tests for the logging system."""
    
    def test_full_logging_workflow(self):
        """Test a complete logging workflow."""
        log_capture = StringIO()
        
        # Create logger with custom handler
        logger = ChatbotLogger("integration_test")
        logger.logger.handlers.clear()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        logger.logger.addHandler(handler)
        
        # Log various types of messages
        logger.info("Starting process", agent="RouterAgent", conversation_id="conv-123")
        logger.debug("Debug information", metadata={"debug_data": "value"})
        logger.error("Error occurred", error_details="Something went wrong")
        
        # Parse all log entries
        log_output = log_capture.getvalue()
        log_lines = [line for line in log_output.strip().split("\n") if line]
        
        assert len(log_lines) >= 2  # Info and error should be logged (debug might be filtered)
        
        # Check first log entry (info)
        first_log = json.loads(log_lines[0])
        assert first_log["level"] == "INFO"
        assert first_log["agent"] == "RouterAgent"
        assert first_log["conversation_id"] == "conv-123"
        
        # Check last log entry (error)
        last_log = json.loads(log_lines[-1])
        assert last_log["level"] == "ERROR"
        assert last_log["error_details"] == "Something went wrong"
    
    def test_json_serialization_edge_cases(self):
        """Test JSON serialization with edge cases."""
        log_capture = StringIO()
        
        logger = ChatbotLogger("edge_case_test")
        logger.logger.handlers.clear()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        logger.logger.addHandler(handler)
        
        # Test with complex metadata
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "none_value": None,
            "boolean": True,
        }
        
        logger.info("Complex metadata test", metadata=complex_metadata)
        
        log_output = log_capture.getvalue()
        log_data = json.loads(log_output.strip())
        
        assert log_data["metadata"]["nested"]["key"] == "value"
        assert log_data["metadata"]["list"] == [1, 2, 3]
        assert log_data["metadata"]["none_value"] is None
        assert log_data["metadata"]["boolean"] is True
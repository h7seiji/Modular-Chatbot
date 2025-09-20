"""
Unit tests for core data models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.models.core import (
    Message,
    ConversationContext,
    AgentDecision,
    AgentResponse,
    ChatRequest,
    ChatResponse
)


class TestMessage:
    """Test cases for Message model."""
    
    def test_message_creation_valid(self):
        """Test creating a valid message."""
        message = Message(
            content="Hello, world!",
            sender="user"
        )
        
        assert message.content == "Hello, world!"
        assert message.sender == "user"
        assert isinstance(message.timestamp, datetime)
        assert message.agent_type is None
    
    def test_message_with_agent_type(self):
        """Test creating a message with agent type."""
        message = Message(
            content="Response from agent",
            sender="agent",
            agent_type="KnowledgeAgent"
        )
        
        assert message.content == "Response from agent"
        assert message.sender == "agent"
        assert message.agent_type == "KnowledgeAgent"
    
    def test_message_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Message()
        
        with pytest.raises(ValidationError):
            Message(content="Hello")
        
        with pytest.raises(ValidationError):
            Message(sender="user")
    
    def test_message_custom_timestamp(self):
        """Test message with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        message = Message(
            content="Test message",
            sender="user",
            timestamp=custom_time
        )
        
        assert message.timestamp == custom_time


class TestConversationContext:
    """Test cases for ConversationContext model."""
    
    def test_conversation_context_creation_valid(self):
        """Test creating a valid conversation context."""
        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456"
        )
        
        assert context.conversation_id == "conv-123"
        assert context.user_id == "user-456"
        assert isinstance(context.timestamp, datetime)
        assert context.message_history == []
    
    def test_conversation_context_with_messages(self):
        """Test conversation context with message history."""
        messages = [
            Message(content="Hello", sender="user"),
            Message(content="Hi there!", sender="agent", agent_type="RouterAgent")
        ]
        
        context = ConversationContext(
            conversation_id="conv-123",
            user_id="user-456",
            message_history=messages
        )
        
        assert len(context.message_history) == 2
        assert context.message_history[0].content == "Hello"
        assert context.message_history[1].agent_type == "RouterAgent"
    
    def test_conversation_context_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ConversationContext()
        
        with pytest.raises(ValidationError):
            ConversationContext(conversation_id="conv-123")
        
        with pytest.raises(ValidationError):
            ConversationContext(user_id="user-456")


class TestAgentDecision:
    """Test cases for AgentDecision model."""
    
    def test_agent_decision_creation_valid(self):
        """Test creating a valid agent decision."""
        decision = AgentDecision(
            selected_agent="MathAgent",
            confidence=0.95,
            reasoning="Mathematical expression detected"
        )
        
        assert decision.selected_agent == "MathAgent"
        assert decision.confidence == 0.95
        assert decision.reasoning == "Mathematical expression detected"
        assert decision.alternatives == []
    
    def test_agent_decision_with_alternatives(self):
        """Test agent decision with alternatives."""
        decision = AgentDecision(
            selected_agent="KnowledgeAgent",
            confidence=0.75,
            reasoning="Knowledge query detected",
            alternatives=["MathAgent", "FallbackAgent"]
        )
        
        assert decision.alternatives == ["MathAgent", "FallbackAgent"]
    
    def test_agent_decision_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence scores
        AgentDecision(selected_agent="Test", confidence=0.0, reasoning="Test")
        AgentDecision(selected_agent="Test", confidence=1.0, reasoning="Test")
        AgentDecision(selected_agent="Test", confidence=0.5, reasoning="Test")
        
        # Invalid confidence scores
        with pytest.raises(ValidationError):
            AgentDecision(selected_agent="Test", confidence=-0.1, reasoning="Test")
        
        with pytest.raises(ValidationError):
            AgentDecision(selected_agent="Test", confidence=1.1, reasoning="Test")
    
    def test_agent_decision_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentDecision()
        
        with pytest.raises(ValidationError):
            AgentDecision(selected_agent="Test")
        
        with pytest.raises(ValidationError):
            AgentDecision(confidence=0.5, reasoning="Test")


class TestAgentResponse:
    """Test cases for AgentResponse model."""
    
    def test_agent_response_creation_valid(self):
        """Test creating a valid agent response."""
        response = AgentResponse(
            content="The answer is 42",
            source_agent="MathAgent",
            execution_time=0.123
        )
        
        assert response.content == "The answer is 42"
        assert response.source_agent == "MathAgent"
        assert response.execution_time == 0.123
        assert response.metadata == {}
        assert response.sources is None
    
    def test_agent_response_with_metadata_and_sources(self):
        """Test agent response with metadata and sources."""
        metadata = {"calculation_type": "arithmetic", "complexity": "simple"}
        sources = ["https://example.com/doc1", "https://example.com/doc2"]
        
        response = AgentResponse(
            content="Based on the documentation...",
            source_agent="KnowledgeAgent",
            execution_time=0.456,
            metadata=metadata,
            sources=sources
        )
        
        assert response.metadata == metadata
        assert response.sources == sources
    
    def test_agent_response_execution_time_validation(self):
        """Test execution time validation."""
        # Valid execution times
        AgentResponse(content="Test", source_agent="Test", execution_time=0.0)
        AgentResponse(content="Test", source_agent="Test", execution_time=1.5)
        
        # Invalid execution time
        with pytest.raises(ValidationError):
            AgentResponse(content="Test", source_agent="Test", execution_time=-0.1)
    
    def test_agent_response_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentResponse()
        
        with pytest.raises(ValidationError):
            AgentResponse(content="Test")
        
        with pytest.raises(ValidationError):
            AgentResponse(source_agent="Test", execution_time=0.1)


class TestChatRequest:
    """Test cases for ChatRequest model."""
    
    def test_chat_request_creation_valid(self):
        """Test creating a valid chat request."""
        request = ChatRequest(
            message="What is 2 + 2?",
            user_id="user-123",
            conversation_id="conv-456"
        )
        
        assert request.message == "What is 2 + 2?"
        assert request.user_id == "user-123"
        assert request.conversation_id == "conv-456"
    
    def test_chat_request_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ChatRequest()
        
        with pytest.raises(ValidationError):
            ChatRequest(message="Test")
        
        with pytest.raises(ValidationError):
            ChatRequest(message="Test", user_id="user-123")


class TestChatResponse:
    """Test cases for ChatResponse model."""
    
    def test_chat_response_creation_valid(self):
        """Test creating a valid chat response."""
        workflow = [
            {"agent": "RouterAgent", "decision": "route_to_math"},
            {"agent": "MathAgent", "decision": "calculate"}
        ]
        
        response = ChatResponse(
            response="The answer is 4",
            source_agent_response="MathAgent",
            agent_workflow=workflow
        )
        
        assert response.response == "The answer is 4"
        assert response.source_agent_response == "MathAgent"
        assert response.agent_workflow == workflow
    
    def test_chat_response_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ChatResponse()
        
        with pytest.raises(ValidationError):
            ChatResponse(response="Test")
        
        with pytest.raises(ValidationError):
            ChatResponse(response="Test", source_agent_response="Agent")
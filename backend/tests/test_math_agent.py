"""
Unit tests for MathAgent simple expression processing.
"""
import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime
from agents.gemini_math_agent import MathAgent
from models.core import ConversationContext, Message


@pytest.fixture
def math_agent():
    """Create a MathAgent instance for testing."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        return MathAgent()


@pytest.fixture
def conversation_context():
    """Create a test conversation context."""
    return ConversationContext(
        conversation_id="test-conv-123",
        user_id="test-user-456",
        timestamp=datetime.utcnow(),
        message_history=[
            Message(
                content="Hello",
                sender="user",
                timestamp=datetime.utcnow()
            )
        ]
    )


class TestSimpleExpressionDetection:
    """Test simple mathematical expression detection."""
    
    def test_can_handle_basic_arithmetic(self, math_agent):
        """Test detection of basic arithmetic expressions."""
        test_cases = [
            ("What is 5 + 3?", 1.0),
            ("Calculate 10 * 2", 1.0),
            ("How much is 65 x 3.11?", 1.0),
            ("Solve 70 + 12", 1.0),
            ("What's (42 * 2) / 6?", 1.0),
        ]
        
        for message, expected_min_confidence in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for: {message}"
    
    def test_can_handle_simple_expressions(self, math_agent):
        """Test detection of simple mathematical expressions."""
        test_cases = [
            ("Calculate sqrt(16)", 0.5),  # keyword + digit
            ("What is 2^3?", 0.5),      # keyword + digit
            ("Solve 3.14 * 2.5", 1.0),  # keyword + operators
            ("What's the result of (5 + 3) * 2?", 1.0)  # keyword + operators
        ]

        for message, expected_min_confidence in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for: {message}"
    
    def test_can_handle_keyword_based(self, math_agent):
        """Test detection based on mathematical keywords."""
        test_cases = [
            ("Please calculate this for me", 0.0),  # keyword but no digits
            ("I need to solve a math problem", 0.0),  # keyword but no digits
            ("Can you compute the answer?", 0.0),  # keyword but no digits
        ]

        for message, expected_min_confidence in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence == expected_min_confidence, f"Failed for: {message}"
    
    def test_can_handle_non_mathematical(self, math_agent):
        """Test rejection of non-mathematical messages."""
        test_cases = [
            "Hello, how are you?",
            "What's the weather like?",
            "Tell me about InfinitePay services",
            "I need help with my account",
        ]
        
        for message in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence < 0.5, f"Should reject: {message}"


class TestSimpleExpressionProcessing:
    """Test simple expression processing."""
    
    @patch('agents.gemini_math_agent.genai')
    @pytest.mark.asyncio
    async def test_process_simple_addition(self, mock_genai, math_agent, conversation_context):
        """Test processing of simple addition."""
        # Mock the Gemini response
        mock_response = Mock()
        mock_response.text = "Step 1: 5 + 3 = 8\nFinal answer: 8"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        math_agent.model = mock_model
        
        response = await math_agent.process("What is 5 + 3?", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "8" in response.content
        assert response.execution_time > 0
        assert response.metadata["model"] == "gemini-1.5-flash"
    
    @patch('agents.gemini_math_agent.genai')
    @pytest.mark.asyncio
    async def test_process_simple_multiplication(self, mock_genai, math_agent, conversation_context):
        """Test processing of simple multiplication."""
        # Mock the Gemini response
        mock_response = Mock()
        mock_response.text = "Step 1: 65 × 3.11 = 202.15\nFinal answer: 202.15"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        math_agent.model = mock_model
        
        response = await math_agent.process("How much is 65 x 3.11?", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "202.15" in response.content
        assert response.execution_time > 0
        assert response.metadata["model"] == "gemini-1.5-flash"
    
    @patch('agents.gemini_math_agent.genai')
    @pytest.mark.asyncio
    async def test_process_simple_division(self, mock_genai, math_agent, conversation_context):
        """Test processing of simple division."""
        # Mock the Gemini response
        mock_response = Mock()
        mock_response.text = "Step 1: 42 ÷ 6 = 7\nFinal answer: 7"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        math_agent.model = mock_model
        
        response = await math_agent.process("What is 42 / 6?", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "7" in response.content
        assert response.execution_time > 0
        assert response.metadata["model"] == "gemini-1.5-flash"


if __name__ == "__main__":
    pytest.main([__file__])
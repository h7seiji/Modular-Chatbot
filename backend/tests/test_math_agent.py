"""
Unit tests for MathAgent mathematical expression processing.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from backend.agents.math_agent import MathAgent
from backend.models.core import ConversationContext, Message


@pytest.fixture
def math_agent():
    """Create a MathAgent instance for testing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
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


class TestMathAgentInitialization:
    """Test MathAgent initialization and configuration."""
    
    def test_initialization_with_api_key(self):
        """Test successful initialization with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = MathAgent()
            assert agent.name == "MathAgent"
            assert len(agent.keywords) > 0
            assert "calculate" in agent.keywords
            assert "math" in agent.keywords
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                MathAgent()
    
    def test_timeout_configuration(self):
        """Test timeout configuration from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "MATH_AGENT_TIMEOUT": "45"}):
            agent = MathAgent()
            assert agent.timeout == 45


class TestMathematicalExpressionDetection:
    """Test mathematical expression detection capabilities."""
    
    def test_can_handle_basic_arithmetic(self, math_agent):
        """Test detection of basic arithmetic expressions."""
        test_cases = [
            ("What is 5 + 3?", 0.95),
            ("Calculate 10 * 2", 0.95),
            ("How much is 65 x 3.11?", 0.95),
            ("Solve 70 + 12", 0.95),
            ("What's (42 * 2) / 6?", 0.95),
        ]
        
        for message, expected_min_confidence in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for: {message}"
    
    def test_can_handle_complex_expressions(self, math_agent):
        """Test detection of complex mathematical expressions."""
        test_cases = [
            "Calculate sqrt(16)",
            "What is 2^3?",
            "Solve sin(30)",
            "Compute 3.14 * 2.5",
            "What's the result of (5 + 3) * 2?"
        ]
        
        for message in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence >= 0.8, f"Failed for: {message}"
    
    def test_can_handle_keyword_based(self, math_agent):
        """Test detection based on mathematical keywords."""
        test_cases = [
            ("Please calculate this for me", 0.7),
            ("I need to solve a math problem", 0.7),
            ("Can you compute the answer?", 0.7),
            ("What is the arithmetic result?", 0.7),
        ]
        
        for message, expected_min_confidence in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence >= expected_min_confidence, f"Failed for: {message}"
    
    def test_can_handle_non_mathematical(self, math_agent):
        """Test rejection of non-mathematical queries."""
        test_cases = [
            "Hello, how are you?",
            "What's the weather like?",
            "Tell me about InfinitePay services",
            "I need help with my account",
            "What are your capabilities?"
        ]
        
        for message in test_cases:
            confidence = math_agent.can_handle(message)
            assert confidence < 0.5, f"Should reject: {message}"
    
    def test_detect_mathematical_expressions(self, math_agent):
        """Test extraction of mathematical expressions from text."""
        test_cases = [
            ("What is 5 + 3?", ["5 + 3"]),
            ("Calculate 10 * 2.5 and 7 - 4", ["10 * 2.5", "7 - 4"]),
            ("Solve (42 * 2) / 6", ["42 * 2"]),
            ("No math here", []),
        ]
        
        for message, expected_expressions in test_cases:
            expressions = math_agent._detect_mathematical_expressions(message)
            # Check that we found at least the expected expressions
            for expected in expected_expressions:
                assert any(expected in expr for expr in expressions), f"Missing {expected} in {expressions}"


class TestInputValidation:
    """Test input validation and security measures."""
    
    def test_validate_safe_expressions(self, math_agent):
        """Test validation of safe mathematical expressions."""
        safe_expressions = [
            "5 + 3",
            "10 * 2.5",
            "(42 * 2) / 6",
            "sqrt(16)",
            "2^3",
            "sin(30) + cos(45)"
        ]
        
        for expr in safe_expressions:
            assert math_agent._validate_mathematical_input(expr), f"Should be safe: {expr}"
    
    def test_validate_dangerous_expressions(self, math_agent):
        """Test rejection of dangerous expressions."""
        dangerous_expressions = [
            "import os",
            "exec('print(1)')",
            "eval('2+2')",
            "__import__('os')",
            "open('/etc/passwd')",
            "subprocess.call('ls')",
            "os.system('rm -rf /')",
            "sys.exit()"
        ]
        
        for expr in dangerous_expressions:
            assert not math_agent._validate_mathematical_input(expr), f"Should be dangerous: {expr}"
    
    def test_validate_expression_length(self, math_agent):
        """Test rejection of overly long expressions."""
        long_expression = "1 + " * 200 + "1"  # Very long expression
        assert not math_agent._validate_mathematical_input(long_expression)
        
        normal_expression = "1 + 2 + 3"
        assert math_agent._validate_mathematical_input(normal_expression)


class TestLLMIntegration:
    """Test LLM integration for mathematical solving."""
    
    @patch('backend.agents.math_agent.OpenAI')
    def test_solve_with_llm_success(self, mock_openai_class, math_agent):
        """Test successful LLM solving."""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Step 1: 5 + 3 = 8\nFinal answer: 8"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        math_agent.client = mock_client
        
        result = math_agent._solve_with_llm("What is 5 + 3?", ["5 + 3"])
        
        assert "8" in result
        mock_client.chat.completions.create.assert_called_once()
        
        # Check the call arguments
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 500
    
    @patch('backend.agents.math_agent.OpenAI')
    def test_solve_with_llm_api_error(self, mock_openai_class, math_agent):
        """Test LLM API error handling."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        math_agent.client = mock_client
        
        with pytest.raises(RuntimeError, match="Failed to process mathematical expression"):
            math_agent._solve_with_llm("What is 5 + 3?", ["5 + 3"])


class TestMathAgentProcessing:
    """Test complete mathematical query processing."""
    
    @patch('backend.agents.math_agent.OpenAI')
    @pytest.mark.asyncio
    async def test_process_successful_calculation(self, mock_openai_class, math_agent, conversation_context):
        """Test successful mathematical calculation processing."""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Step 1: 65 × 3.11 = 202.15\nFinal answer: 202.15"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        math_agent.client = mock_client
        
        response = await math_agent.process("How much is 65 x 3.11?", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "202.15" in response.content
        assert response.execution_time > 0
        assert "expressions_detected" in response.metadata
        assert response.metadata["model_used"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_process_invalid_input(self, math_agent, conversation_context):
        """Test processing with invalid/dangerous input."""
        response = await math_agent.process("import os; os.system('rm -rf /')", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "error" in response.content.lower()
        assert response.metadata.get("processing_failed") is True
    
    @patch('backend.agents.math_agent.OpenAI')
    @pytest.mark.asyncio
    async def test_process_llm_error(self, mock_openai_class, math_agent, conversation_context):
        """Test processing when LLM fails."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        math_agent.client = mock_client
        
        response = await math_agent.process("What is 5 + 3?", conversation_context)
        
        assert response.source_agent == "MathAgent"
        assert "error" in response.content.lower()
        assert response.metadata.get("processing_failed") is True
        assert "error" in response.metadata


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    @patch('backend.agents.math_agent.OpenAI')
    @pytest.mark.asyncio
    async def test_various_mathematical_queries(self, mock_openai_class, math_agent, conversation_context):
        """Test various types of mathematical queries."""
        # Mock responses for different types of queries
        mock_responses = {
            "5 + 3": "Step 1: 5 + 3 = 8\nFinal answer: 8",
            "65 * 3.11": "Step 1: 65 × 3.11 = 202.15\nFinal answer: 202.15",
            "(42 * 2) / 6": "Step 1: 42 × 2 = 84\nStep 2: 84 ÷ 6 = 14\nFinal answer: 14",
            "sqrt(16)": "Step 1: √16 = 4\nFinal answer: 4"
        }
        
        def mock_create(**kwargs):
            content = kwargs["messages"][1]["content"]
            for expr, response in mock_responses.items():
                if expr in content:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = response
                    return mock_response
            # Default response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Calculation completed"
            return mock_response
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = mock_create
        math_agent.client = mock_client
        
        test_queries = [
            ("What is 5 + 3?", "8"),
            ("How much is 65 x 3.11?", "202.15"),
            ("Calculate (42 * 2) / 6", "14"),
            ("What's sqrt(16)?", "4")
        ]
        
        for query, expected_answer in test_queries:
            response = await math_agent.process(query, conversation_context)
            assert response.source_agent == "MathAgent"
            assert expected_answer in response.content
            assert response.execution_time > 0
            assert len(response.metadata["expressions_detected"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
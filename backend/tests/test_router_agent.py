"""
Unit tests for RouterAgent routing decisions.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from agents.base import RouterAgent, SpecializedAgent
from models.core import ConversationContext, Message, AgentDecision, AgentResponse


class MockMathAgent(SpecializedAgent):
    """Mock math agent for testing."""
    
    def __init__(self):
        super().__init__("MathAgent", keywords=["calculate", "math", "+", "-", "*", "/"])
    
    def can_handle(self, message: str) -> float:
        """Return high confidence for math-related queries."""
        message_lower = message.lower()
        if any(op in message_lower for op in ["+", "-", "*", "/", "calculate", "math"]):
            return 0.95
        return 0.15
    
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """Mock processing for math queries."""
        return AgentResponse(
            content="Math calculation result",
            source_agent="MathAgent",
            execution_time=0.1,
            metadata={"calculation_type": "arithmetic"}
        )


class MockKnowledgeAgent(SpecializedAgent):
    """Mock knowledge agent for testing."""
    
    def __init__(self):
        super().__init__("KnowledgeAgent", keywords=["what", "how", "help", "infinitepay"])
    
    def can_handle(self, message: str) -> float:
        """Return high confidence for knowledge queries."""
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ["what", "how", "help", "infinitepay"]):
            return 0.85
        return 0.2
    
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """Mock processing for knowledge queries."""
        return AgentResponse(
            content="Knowledge base response",
            source_agent="KnowledgeAgent",
            execution_time=0.2,
            metadata={"query_type": "knowledge"},
            sources=["https://example.com/help"]
        )


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


@pytest.fixture
def router_agent():
    """Create a RouterAgent with mock agents."""
    router = RouterAgent()
    router.register_agent(MockMathAgent())
    router.register_agent(MockKnowledgeAgent())
    return router


class TestRouterAgentDecisions:
    """Test RouterAgent routing decisions."""
    
    @pytest.mark.asyncio
    async def test_route_math_query(self, router_agent, conversation_context):
        """Test routing of mathematical queries."""
        decision = await router_agent.route_message("What is 5 + 3?", conversation_context)
        
        assert isinstance(decision, AgentDecision)
        assert decision.selected_agent == "MathAgent"
        assert decision.confidence == 0.95
        assert "MathAgent" in decision.reasoning
        assert "KnowledgeAgent" in decision.alternatives
    
    @pytest.mark.asyncio
    async def test_route_knowledge_query(self, router_agent, conversation_context):
        """Test routing of knowledge queries."""
        decision = await router_agent.route_message("What are InfinitePay fees?", conversation_context)
        
        assert isinstance(decision, AgentDecision)
        assert decision.selected_agent == "KnowledgeAgent"
        assert decision.confidence == 0.85
        assert "KnowledgeAgent" in decision.reasoning
        assert "MathAgent" in decision.alternatives
    
    @pytest.mark.asyncio
    async def test_route_ambiguous_query(self, router_agent, conversation_context):
        """Test routing of ambiguous queries."""
        decision = await router_agent.route_message("Hello there", conversation_context)
        
        assert isinstance(decision, AgentDecision)
        # Should route to KnowledgeAgent as it has higher base confidence (0.2 vs 0.1)
        assert decision.selected_agent == "KnowledgeAgent"
        assert decision.confidence == 0.2
    
    @pytest.mark.asyncio
    async def test_route_with_no_agents(self, conversation_context):
        """Test routing when no agents are registered."""
        router = RouterAgent()
        
        with pytest.raises(ValueError, match="No agents registered"):
            await router.route_message("Test message", conversation_context)
    
    @pytest.mark.asyncio
    async def test_route_confidence_comparison(self, conversation_context):
        """Test that router selects agent with highest confidence."""
        router = RouterAgent()
        
        # Create agents with different confidence levels
        high_confidence_agent = Mock(spec=SpecializedAgent)
        high_confidence_agent.name = "HighAgent"
        high_confidence_agent.can_handle.return_value = 0.9
        
        low_confidence_agent = Mock(spec=SpecializedAgent)
        low_confidence_agent.name = "LowAgent"
        low_confidence_agent.can_handle.return_value = 0.3
        
        router.register_agent(high_confidence_agent)
        router.register_agent(low_confidence_agent)
        
        decision = await router.route_message("Test message", conversation_context)
        
        assert decision.selected_agent == "HighAgent"
        assert decision.confidence == 0.9
        assert "LowAgent" in decision.alternatives


if __name__ == "__main__":
    pytest.main([__file__])
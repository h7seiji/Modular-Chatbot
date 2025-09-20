"""
Unit tests for RouterAgent routing decisions and agent management.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.agents.base import RouterAgent, SpecializedAgent
from backend.models.core import ConversationContext, Message, AgentDecision, AgentResponse


class MockMathAgent(SpecializedAgent):
    """Mock math agent for testing."""
    
    def __init__(self):
        super().__init__("MathAgent", keywords=["calculate", "math", "+", "-", "*", "/"])
    
    def can_handle(self, message: str) -> float:
        """Return high confidence for math-related queries."""
        message_lower = message.lower()
        if any(op in message_lower for op in ["+", "-", "*", "/", "calculate", "math"]):
            return 0.95
        return 0.1
    
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


class TestRouterAgentInitialization:
    """Test RouterAgent initialization and agent registration."""
    
    def test_router_agent_creation(self):
        """Test RouterAgent initialization."""
        router = RouterAgent()
        assert router.name == "RouterAgent"
        assert len(router.agents) == 0
    
    def test_agent_registration(self):
        """Test registering agents with the router."""
        router = RouterAgent()
        math_agent = MockMathAgent()
        knowledge_agent = MockKnowledgeAgent()
        
        router.register_agent(math_agent)
        router.register_agent(knowledge_agent)
        
        assert len(router.agents) == 2
        assert "MathAgent" in router.agents
        assert "KnowledgeAgent" in router.agents
        assert router.agents["MathAgent"] == math_agent
        assert router.agents["KnowledgeAgent"] == knowledge_agent
    
    def test_agent_replacement(self):
        """Test that registering an agent with the same name replaces the old one."""
        router = RouterAgent()
        old_agent = MockMathAgent()
        new_agent = MockMathAgent()
        
        router.register_agent(old_agent)
        assert router.agents["MathAgent"] == old_agent
        
        router.register_agent(new_agent)
        assert router.agents["MathAgent"] == new_agent
        assert len(router.agents) == 1


class TestRouterAgentRouting:
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
    
    @pytest.mark.asyncio
    async def test_alternatives_filtering(self, conversation_context):
        """Test that alternatives are filtered by minimum confidence threshold."""
        router = RouterAgent()
        
        # Create agents with different confidence levels
        high_agent = Mock(spec=SpecializedAgent)
        high_agent.name = "HighAgent"
        high_agent.can_handle.return_value = 0.9
        
        medium_agent = Mock(spec=SpecializedAgent)
        medium_agent.name = "MediumAgent"
        medium_agent.can_handle.return_value = 0.3
        
        low_agent = Mock(spec=SpecializedAgent)
        low_agent.name = "LowAgent"
        low_agent.can_handle.return_value = 0.05  # Below 0.1 threshold
        
        router.register_agent(high_agent)
        router.register_agent(medium_agent)
        router.register_agent(low_agent)
        
        decision = await router.route_message("Test message", conversation_context)
        
        assert decision.selected_agent == "HighAgent"
        assert "MediumAgent" in decision.alternatives
        assert "LowAgent" not in decision.alternatives  # Below threshold


class TestRouterAgentProcessing:
    """Test RouterAgent message processing."""
    
    @pytest.mark.asyncio
    async def test_process_math_query(self, router_agent, conversation_context):
        """Test processing of mathematical queries."""
        response = await router_agent.process("Calculate 10 + 5", conversation_context)
        
        assert isinstance(response, AgentResponse)
        assert response.source_agent == "MathAgent"
        assert response.content == "Math calculation result"
        assert response.execution_time == 0.1
        assert response.metadata["calculation_type"] == "arithmetic"
    
    @pytest.mark.asyncio
    async def test_process_knowledge_query(self, router_agent, conversation_context):
        """Test processing of knowledge queries."""
        response = await router_agent.process("What is InfinitePay?", conversation_context)
        
        assert isinstance(response, AgentResponse)
        assert response.source_agent == "KnowledgeAgent"
        assert response.content == "Knowledge base response"
        assert response.execution_time == 0.2
        assert response.metadata["query_type"] == "knowledge"
        assert response.sources == ["https://example.com/help"]
    
    @pytest.mark.asyncio
    async def test_process_with_agent_error(self, conversation_context):
        """Test processing when selected agent raises an error."""
        router = RouterAgent()
        
        # Create a mock agent that raises an error
        failing_agent = Mock(spec=SpecializedAgent)
        failing_agent.name = "FailingAgent"
        failing_agent.can_handle.return_value = 0.9
        failing_agent.process = AsyncMock(side_effect=Exception("Agent processing failed"))
        
        router.register_agent(failing_agent)
        
        with pytest.raises(Exception, match="Agent processing failed"):
            await router_agent.process("Test message", conversation_context)
    
    def test_router_can_handle(self, router_agent):
        """Test that router can handle any message."""
        assert router_agent.can_handle("Any message") == 1.0
        assert router_agent.can_handle("") == 1.0
        assert router_agent.can_handle("Complex mathematical expression") == 1.0


class TestRouterAgentEdgeCases:
    """Test RouterAgent edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_route_empty_message(self, router_agent, conversation_context):
        """Test routing of empty messages."""
        decision = await router_agent.route_message("", conversation_context)
        
        assert isinstance(decision, AgentDecision)
        # Should still route to an agent (likely KnowledgeAgent with higher base confidence)
        assert decision.selected_agent in ["MathAgent", "KnowledgeAgent"]
    
    @pytest.mark.asyncio
    async def test_route_very_long_message(self, router_agent, conversation_context):
        """Test routing of very long messages."""
        long_message = "Calculate " + "1 + " * 1000 + "1"
        decision = await router_agent.route_message(long_message, conversation_context)
        
        assert isinstance(decision, AgentDecision)
        assert decision.selected_agent == "MathAgent"  # Should detect math content
    
    @pytest.mark.asyncio
    async def test_route_special_characters(self, router_agent, conversation_context):
        """Test routing of messages with special characters."""
        special_message = "What is 5 + 3? 🤔 #math @help"
        decision = await router_agent.route_message(special_message, conversation_context)
        
        assert isinstance(decision, AgentDecision)
        assert decision.selected_agent == "MathAgent"  # Should detect math despite special chars
    
    @pytest.mark.asyncio
    async def test_multiple_routing_calls(self, router_agent, conversation_context):
        """Test multiple routing calls with the same router."""
        messages = [
            "What is 2 + 2?",
            "How does InfinitePay work?",
            "Calculate 10 * 5",
            "What are the fees?"
        ]
        
        expected_agents = ["MathAgent", "KnowledgeAgent", "MathAgent", "KnowledgeAgent"]
        
        for message, expected_agent in zip(messages, expected_agents):
            decision = await router_agent.route_message(message, conversation_context)
            assert decision.selected_agent == expected_agent
    
    @pytest.mark.asyncio
    async def test_agent_confidence_edge_cases(self, conversation_context):
        """Test routing with edge case confidence values."""
        router = RouterAgent()
        
        # Agent that returns exactly 0.0 confidence
        zero_agent = Mock(spec=SpecializedAgent)
        zero_agent.name = "ZeroAgent"
        zero_agent.can_handle.return_value = 0.0
        
        # Agent that returns exactly 1.0 confidence
        perfect_agent = Mock(spec=SpecializedAgent)
        perfect_agent.name = "PerfectAgent"
        perfect_agent.can_handle.return_value = 1.0
        
        router.register_agent(zero_agent)
        router.register_agent(perfect_agent)
        
        decision = await router_agent.route_message("Test", conversation_context)
        assert decision.selected_agent == "PerfectAgent"
        assert decision.confidence == 1.0
        assert "ZeroAgent" not in decision.alternatives  # Below 0.1 threshold


class TestRouterAgentIntegration:
    """Integration tests for RouterAgent with realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, router_agent):
        """Test a complete conversation flow through the router."""
        # Simulate a conversation with multiple turns
        conversation_id = "conv-integration-test"
        user_id = "user-integration-test"
        
        messages = [
            ("Hello, I need help", "KnowledgeAgent"),
            ("What is 5 + 3?", "MathAgent"),
            ("How much are InfinitePay fees?", "KnowledgeAgent"),
            ("Calculate 10 * 2.5", "MathAgent"),
        ]
        
        message_history = []
        
        for message_content, expected_agent in messages:
            # Add user message to history
            user_message = Message(
                content=message_content,
                sender="user",
                timestamp=datetime.utcnow()
            )
            message_history.append(user_message)
            
            # Create context with growing history
            context = ConversationContext(
                conversation_id=conversation_id,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                message_history=message_history.copy()
            )
            
            # Route and process message
            decision = await router_agent.route_message(message_content, context)
            response = await router_agent.process(message_content, context)
            
            # Verify routing
            assert decision.selected_agent == expected_agent
            assert response.source_agent == expected_agent
            
            # Add agent response to history
            agent_message = Message(
                content=response.content,
                sender="agent",
                timestamp=datetime.utcnow(),
                agent_type=response.source_agent
            )
            message_history.append(agent_message)
    
    @pytest.mark.asyncio
    async def test_concurrent_routing(self, router_agent, conversation_context):
        """Test concurrent routing requests."""
        import asyncio
        
        messages = [
            "What is 2 + 2?",
            "How does InfinitePay work?",
            "Calculate 15 / 3",
            "What are the payment options?",
            "Solve 7 * 8"
        ]
        
        # Process all messages concurrently
        tasks = [
            router_agent.route_message(message, conversation_context)
            for message in messages
        ]
        
        decisions = await asyncio.gather(*tasks)
        
        # Verify all decisions are valid
        assert len(decisions) == len(messages)
        for decision in decisions:
            assert isinstance(decision, AgentDecision)
            assert decision.selected_agent in ["MathAgent", "KnowledgeAgent"]
            assert 0.0 <= decision.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_performance_tracking(self, router_agent, conversation_context):
        """Test that agent performance can be tracked through multiple calls."""
        math_queries = [
            "What is 1 + 1?",
            "Calculate 5 * 6",
            "Solve 100 / 4",
            "What is 2^3?"
        ]
        
        math_responses = []
        for query in math_queries:
            response = await router_agent.process(query, conversation_context)
            math_responses.append(response)
        
        # Verify all responses came from MathAgent
        assert all(r.source_agent == "MathAgent" for r in math_responses)
        
        # Verify execution times are recorded
        assert all(r.execution_time > 0 for r in math_responses)
        
        # Calculate average response time
        avg_time = sum(r.execution_time for r in math_responses) / len(math_responses)
        assert avg_time > 0


if __name__ == "__main__":
    pytest.main([__file__])
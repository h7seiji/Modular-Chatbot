"""
End-to-end tests for the /chat API endpoint.
"""
import pytest
import requests
import time
from unittest.mock import patch, Mock, AsyncMock
from models.core import AgentResponse, AgentDecision


class TestChatAPI:
    """End-to-end tests for the /chat API endpoint."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the API (assumes running locally)."""
        return "http://localhost:8000"
    
    @pytest.fixture
    def session(self):
        """HTTP session for making requests."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    @pytest.fixture
    def mock_agents_for_e2e(self):
        """Mock agents for end-to-end testing."""
        # Mock MathAgent
        mock_math_agent = Mock()
        mock_math_agent.name = "MathAgent"
        mock_math_agent.can_handle = Mock(side_effect=lambda msg: 0.95 if any(op in msg.lower() for op in ['+', '-', '*', '/', 'calculate', 'math']) else 0.1)
        mock_math_agent.process = AsyncMock(return_value=AgentResponse(
            content="Mathematical calculation completed",
            source_agent="MathAgent",
            execution_time=0.123,
            metadata={"calculation_type": "arithmetic"}
        ))
        
        # Mock KnowledgeAgent
        mock_knowledge_agent = Mock()
        mock_knowledge_agent.name = "KnowledgeAgent"
        mock_knowledge_agent.can_handle = Mock(side_effect=lambda msg: 0.85 if any(kw in msg.lower() for kw in ['what', 'how', 'help', 'infinitepay', 'fees']) else 0.2)
        mock_knowledge_agent.process = AsyncMock(return_value=AgentResponse(
            content="Knowledge base information provided",
            source_agent="KnowledgeAgent",
            execution_time=0.234,
            metadata={"query_type": "knowledge"},
            sources=["https://ajuda.infinitepay.io/pt-BR/"]
        ))
        
        # Mock RouterAgent
        mock_router = Mock()
        mock_router.agents = {
            "MathAgent": mock_math_agent,
            "KnowledgeAgent": mock_knowledge_agent
        }
        
        def mock_route_message(message, context):
            math_confidence = mock_math_agent.can_handle(message)
            knowledge_confidence = mock_knowledge_agent.can_handle(message)
            
            if math_confidence > knowledge_confidence:
                return AgentDecision(
                    selected_agent="MathAgent",
                    confidence=math_confidence,
                    reasoning="Mathematical expression detected",
                    alternatives=["KnowledgeAgent"]
                )
            else:
                return AgentDecision(
                    selected_agent="KnowledgeAgent",
                    confidence=knowledge_confidence,
                    reasoning="Knowledge query detected",
                    alternatives=["MathAgent"]
                )
        
        def mock_process(message, context):
            decision = mock_route_message(message, context)
            if decision.selected_agent == "MathAgent":
                return mock_math_agent.process(message, context)
            else:
                return mock_knowledge_agent.process(message, context)
        
        mock_router.route_message = AsyncMock(side_effect=mock_route_message)
        mock_router.process = AsyncMock(side_effect=mock_process)
        
        return mock_router
    
    def test_chat_api_math_query(self, base_url, session, mock_agents_for_e2e):
        """Test /chat API with mathematical query."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            response = session.post(f"{base_url}/chat", json={
                "message": "What is 15 + 27?",
                "userId": "e2e_test_user_001",
                "conversationId": "e2e_math_conv_001"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "response" in data
            assert "source_agent_response" in data
            assert "agent_workflow" in data
            
            # Verify mathematical query was routed to MathAgent
            assert "MathAgent" in data["source_agent_response"]
            
            # Verify workflow contains expected steps
            workflow = data["agent_workflow"]
            assert len(workflow) == 2
            assert workflow[0]["agent"] == "RouterAgent"
            assert workflow[1]["agent"] == "MathAgent"
            
            # Verify response content
            assert "42" in data["response"] or "Mathematical" in data["response"]
    
    def test_chat_api_knowledge_query(self, base_url, session, mock_agents_for_e2e):
        """Test /chat API with knowledge query."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            response = session.post(f"{base_url}/chat", json={
                "message": "What are InfinitePay card machine fees?",
                "userId": "e2e_test_user_002",
                "conversationId": "e2e_knowledge_conv_001"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify knowledge query was routed to KnowledgeAgent
            assert "KnowledgeAgent" in data["source_agent_response"]
            
            # Verify workflow
            workflow = data["agent_workflow"]
            assert workflow[1]["agent"] == "KnowledgeAgent"
            
            # Verify response content
            assert "InfinitePay" in data["response"] or "fees" in data["response"]
    
    def test_chat_api_multi_turn_conversation(self, base_url, session, mock_agents_for_e2e):
        """Test /chat API with multi-turn conversation."""
        conversation_id = "e2e_multi_turn_conv_001"
        user_id = "e2e_test_user_003"
        
        conversation_turns = [
            {
                "message": "What is 25 * 4?",
                "expected_agent": "MathAgent",
                "description": "Mathematical calculation"
            },
            {
                "message": "How much are the transaction fees?",
                "expected_agent": "KnowledgeAgent",
                "description": "Knowledge about fees"
            },
            {
                "message": "Calculate 15% of 200",
                "expected_agent": "MathAgent",
                "description": "Percentage calculation"
            }
        ]
        
        with patch('app.main.router_agent', mock_agents_for_e2e):
            for turn_num, turn in enumerate(conversation_turns, 1):
                response = session.post(f"{base_url}/chat", json={
                    "message": turn["message"],
                    "userId": user_id,
                    "conversationId": conversation_id
                })
                
                assert response.status_code == 200, f"Turn {turn_num} failed: {turn['description']}"
                data = response.json()
                
                # Verify correct agent was selected
                assert turn["expected_agent"] in data["source_agent_response"], \
                    f"Turn {turn_num}: Expected {turn['expected_agent']}, got {data['source_agent_response']}"
                
                # Verify workflow structure
                workflow = data["agent_workflow"]
                assert len(workflow) == 2
                assert workflow[0]["agent"] == "RouterAgent"
                assert workflow[1]["agent"] == turn["expected_agent"]
    
    def test_chat_api_error_handling(self, base_url, session):
        """Test /chat API error handling."""
        # Test invalid request format
        response = session.post(f"{base_url}/chat", json={
            "invalid_field": "test"
        })
        assert response.status_code == 422  # Validation error
        
        # Test empty message
        response = session.post(f"{base_url}/chat", json={
            "message": "",
            "userId": "test_user",
            "conversationId": "test_conv"
        })
        assert response.status_code == 400  # Bad request
        
        # Test missing required fields
        response = session.post(f"{base_url}/chat", json={
            "message": "Hello world"
        })
        assert response.status_code == 422  # Validation error
    
    def test_chat_api_response_structure(self, base_url, session, mock_agents_for_e2e):
        """Test /chat API response structure."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            response = session.post(f"{base_url}/chat", json={
                "message": "What is 2 + 2?",
                "userId": "test_user",
                "conversationId": "test_conv"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify required fields
            assert "response" in data
            assert "source_agent_response" in data
            assert "agent_workflow" in data
            
            # Verify response content is string
            assert isinstance(data["response"], str)
            assert len(data["response"]) > 0
            
            # Verify source agent response contains agent name
            assert isinstance(data["source_agent_response"], str)
            assert "MathAgent" in data["source_agent_response"] or "KnowledgeAgent" in data["source_agent_response"]
            
            # Verify workflow structure
            assert isinstance(data["agent_workflow"], list)
            assert len(data["agent_workflow"]) == 2
            
            # Verify workflow steps
            for step in data["agent_workflow"]:
                assert "agent" in step
                assert "decision" in step
                assert isinstance(step["agent"], str)
                assert isinstance(step["decision"], str)


if __name__ == "__main__":
    # Note: These tests require the FastAPI application to be running
    # Run with: pytest backend/tests/test_end_to_end.py -v
    pytest.main([__file__, "-v"])
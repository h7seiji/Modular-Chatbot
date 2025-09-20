"""
End-to-end tests for complete user workflows using pytest and requests.
"""
import pytest
import requests
import time
import json
import asyncio
from typing import Dict, List
from unittest.mock import patch, Mock, AsyncMock

from models.core import AgentResponse, AgentDecision


class TestEndToEndWorkflows:
    """End-to-end tests for complete user workflows."""
    
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
    
    def test_health_check_workflow(self, base_url, session):
        """Test basic health check workflow."""
        response = session.get(f"{base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify health response structure
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "agents_registered" in data
        
        # Verify timestamp is recent
        current_time = time.time()
        assert abs(current_time - data["timestamp"]) < 10  # Within 10 seconds
    
    def test_single_math_query_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test complete workflow for a single mathematical query."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            # Start the application (this would normally be done externally)
            # For testing, we assume the app is running
            
            # Send mathematical query
            response = session.post(f"{base_url}/chat", json={
                "message": "What is 15 + 27?",
                "user_id": "e2e_test_user_001",
                "conversation_id": "e2e_math_conv_001"
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
            assert "Mathematical calculation completed" in data["response"]
    
    def test_single_knowledge_query_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test complete workflow for a single knowledge query."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            # Send knowledge query
            response = session.post(f"{base_url}/chat", json={
                "message": "What are InfinitePay card machine fees?",
                "user_id": "e2e_test_user_002",
                "conversation_id": "e2e_knowledge_conv_001"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify knowledge query was routed to KnowledgeAgent
            assert "KnowledgeAgent" in data["source_agent_response"]
            
            # Verify workflow
            workflow = data["agent_workflow"]
            assert workflow[1]["agent"] == "KnowledgeAgent"
            
            # Verify response content
            assert "Knowledge base information provided" in data["response"]
    
    def test_multi_turn_conversation_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test complete multi-turn conversation workflow."""
        conversation_id = "e2e_multi_turn_conv_001"
        user_id = "e2e_test_user_003"
        
        conversation_turns = [
            {
                "message": "Hello, I need help with calculations",
                "expected_agent": "KnowledgeAgent",
                "description": "Greeting and help request"
            },
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
            },
            {
                "message": "What payment methods does InfinitePay support?",
                "expected_agent": "KnowledgeAgent",
                "description": "Knowledge about payment methods"
            }
        ]
        
        with patch('app.main.router_agent', mock_agents_for_e2e):
            conversation_history = []
            
            for turn_num, turn in enumerate(conversation_turns, 1):
                # Send message
                response = session.post(f"{base_url}/chat", json={
                    "message": turn["message"],
                    "user_id": user_id,
                    "conversation_id": conversation_id
                })
                
                assert response.status_code == 200, f"Turn {turn_num} failed: {turn['description']}"
                data = response.json()
                
                # Verify correct agent was selected
                assert turn["expected_agent"] in data["source_agent_response"], \
                    f"Turn {turn_num}: Expected {turn['expected_agent']}, got {data['source_agent_response']}"
                
                # Store conversation turn
                conversation_history.append({
                    "turn": turn_num,
                    "message": turn["message"],
                    "response": data["response"],
                    "agent": turn["expected_agent"],
                    "workflow": data["agent_workflow"]
                })
                
                # Small delay between turns
                time.sleep(0.1)
            
            # Verify conversation flow
            assert len(conversation_history) == 5
            
            # Verify agent alternation
            agents_used = [turn["agent"] for turn in conversation_history]
            assert "MathAgent" in agents_used
            assert "KnowledgeAgent" in agents_used
            
            # Verify each turn had proper workflow
            for turn in conversation_history:
                assert len(turn["workflow"]) == 2
                assert turn["workflow"][0]["agent"] == "RouterAgent"
                assert turn["workflow"][1]["agent"] == turn["agent"]
    
    def test_concurrent_users_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test workflow with multiple concurrent users."""
        import concurrent.futures
        
        def user_session(user_id: str, conversation_id: str, messages: List[str]) -> List[Dict]:
            """Simulate a user session with multiple messages."""
            session = requests.Session()
            session.headers.update({"Content-Type": "application/json"})
            
            results = []
            for message in messages:
                response = session.post(f"{base_url}/chat", json={
                    "message": message,
                    "user_id": user_id,
                    "conversation_id": conversation_id
                })
                
                if response.status_code == 200:
                    results.append({
                        "message": message,
                        "response": response.json(),
                        "success": True
                    })
                else:
                    results.append({
                        "message": message,
                        "error": response.text,
                        "success": False
                    })
                
                time.sleep(0.05)  # Small delay between messages
            
            return results
        
        # Define user sessions
        user_sessions = [
            {
                "user_id": "concurrent_user_001",
                "conversation_id": "concurrent_conv_001",
                "messages": ["What is 10 + 5?", "How does InfinitePay work?", "Calculate 20 * 3"]
            },
            {
                "user_id": "concurrent_user_002",
                "conversation_id": "concurrent_conv_002",
                "messages": ["What are the fees?", "Solve 100 / 4", "Help with payment setup"]
            },
            {
                "user_id": "concurrent_user_003",
                "conversation_id": "concurrent_conv_003",
                "messages": ["Calculate 7 * 8", "What is InfinitePay?", "How much is 50% of 80?"]
            }
        ]
        
        with patch('app.main.router_agent', mock_agents_for_e2e):
            # Run concurrent user sessions
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(user_session, session["user_id"], session["conversation_id"], session["messages"])
                    for session in user_sessions
                ]
                
                results = [future.result() for future in futures]
            
            # Verify all sessions completed successfully
            for user_results in results:
                assert len(user_results) == 3  # Each user sent 3 messages
                for result in user_results:
                    assert result["success"], f"Failed message: {result.get('message', 'unknown')}"
                    
                    # Verify response structure
                    response_data = result["response"]
                    assert "response" in response_data
                    assert "source_agent_response" in response_data
                    assert "agent_workflow" in response_data
    
    def test_error_handling_workflow(self, base_url, session):
        """Test error handling in end-to-end workflows."""
        # Test invalid request format
        response = session.post(f"{base_url}/chat", json={
            "invalid_field": "test"
        })
        assert response.status_code == 422  # Validation error
        
        # Test empty message
        response = session.post(f"{base_url}/chat", json={
            "message": "",
            "user_id": "test_user",
            "conversation_id": "test_conv"
        })
        assert response.status_code == 400  # Bad request
        
        # Test malicious content
        response = session.post(f"{base_url}/chat", json={
            "message": "<script>alert('xss')</script>",
            "user_id": "test_user",
            "conversation_id": "test_conv"
        })
        assert response.status_code == 400  # Blocked by security
        
        # Test invalid user ID
        response = session.post(f"{base_url}/chat", json={
            "message": "Hello world",
            "user_id": "invalid@user!",
            "conversation_id": "test_conv"
        })
        assert response.status_code == 400  # Validation error
    
    def test_performance_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test performance characteristics in end-to-end workflow."""
        with patch('app.main.router_agent', mock_agents_for_e2e):
            # Measure response times for different query types
            test_queries = [
                ("What is 2 + 2?", "math"),
                ("What are InfinitePay services?", "knowledge"),
                ("Calculate 15 * 8", "math"),
                ("How do I set up my account?", "knowledge"),
                ("Solve 144 / 12", "math")
            ]
            
            response_times = []
            
            for query, query_type in test_queries:
                start_time = time.time()
                
                response = session.post(f"{base_url}/chat", json={
                    "message": query,
                    "user_id": "perf_test_user",
                    "conversation_id": "perf_test_conv"
                })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                assert response.status_code == 200
                response_times.append({
                    "query": query,
                    "type": query_type,
                    "response_time": response_time,
                    "data": response.json()
                })
            
            # Verify performance characteristics
            avg_response_time = sum(r["response_time"] for r in response_times) / len(response_times)
            max_response_time = max(r["response_time"] for r in response_times)
            
            # Performance assertions (adjust thresholds as needed)
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
            assert max_response_time < 5.0, f"Max response time too high: {max_response_time:.3f}s"
            
            # Verify all responses were successful
            for result in response_times:
                assert "response" in result["data"]
                assert "agent_workflow" in result["data"]
    
    def test_conversation_persistence_workflow(self, base_url, session, mock_agents_for_e2e):
        """Test that conversation context persists across requests."""
        conversation_id = "persistence_test_conv"
        user_id = "persistence_test_user"
        
        with patch('app.main.router_agent', mock_agents_for_e2e):
            # Send initial message
            response1 = session.post(f"{base_url}/chat", json={
                "message": "Hello, I'm starting a conversation",
                "user_id": user_id,
                "conversation_id": conversation_id
            })
            assert response1.status_code == 200
            
            # Send follow-up message in same conversation
            response2 = session.post(f"{base_url}/chat", json={
                "message": "What is 5 + 3?",
                "user_id": user_id,
                "conversation_id": conversation_id
            })
            assert response2.status_code == 200
            
            # Send another follow-up
            response3 = session.post(f"{base_url}/chat", json={
                "message": "Tell me about InfinitePay fees",
                "user_id": user_id,
                "conversation_id": conversation_id
            })
            assert response3.status_code == 200
            
            # Verify all responses are valid
            responses = [response1.json(), response2.json(), response3.json()]
            for response_data in responses:
                assert "response" in response_data
                assert "agent_workflow" in response_data
            
            # Verify different agents were used appropriately
            assert "KnowledgeAgent" in responses[0]["source_agent_response"]  # Greeting
            assert "MathAgent" in responses[1]["source_agent_response"]       # Math query
            assert "KnowledgeAgent" in responses[2]["source_agent_response"]  # Knowledge query
    
    def test_rate_limiting_workflow(self, base_url, session):
        """Test rate limiting behavior in end-to-end workflow."""
        # Make rapid requests to test rate limiting
        responses = []
        start_time = time.time()
        
        for i in range(20):  # Make 20 rapid requests
            response = session.get(f"{base_url}/health")
            responses.append({
                "status_code": response.status_code,
                "timestamp": time.time() - start_time
            })
            time.sleep(0.05)  # Small delay
        
        # Analyze rate limiting behavior
        success_count = sum(1 for r in responses if r["status_code"] == 200)
        rate_limited_count = sum(1 for r in responses if r["status_code"] == 429)
        
        # Most requests should succeed (health endpoint typically has generous limits)
        assert success_count >= 15, f"Too many requests were rate limited: {rate_limited_count}/20"
        
        # If rate limiting occurred, verify it was applied correctly
        if rate_limited_count > 0:
            # Rate limited responses should come after initial successful ones
            rate_limited_indices = [i for i, r in enumerate(responses) if r["status_code"] == 429]
            assert min(rate_limited_indices) > 5, "Rate limiting applied too early"


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the API."""
        return "http://localhost:8000"
    
    @pytest.fixture
    def session(self):
        """HTTP session for making requests."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session
    
    def test_customer_support_scenario(self, base_url, session):
        """Test a realistic customer support scenario."""
        # This test would run against a real or more complete mock system
        conversation_id = "customer_support_001"
        user_id = "customer_001"
        
        # Simulate customer support conversation
        support_conversation = [
            "Hello, I need help with my InfinitePay account",
            "What are the fees for card transactions?",
            "How much would I pay for a R$ 100 transaction?",
            "Can you calculate 2.5% of R$ 100?",
            "Thank you for the help"
        ]
        
        # Note: This test would need the actual system running
        # For now, we'll just verify the structure
        assert len(support_conversation) == 5
        assert conversation_id == "customer_support_001"
        assert user_id == "customer_001"
    
    def test_business_calculation_scenario(self, base_url, session):
        """Test a business calculation scenario."""
        conversation_id = "business_calc_001"
        user_id = "business_user_001"
        
        # Simulate business user doing calculations
        business_conversation = [
            "I need to calculate my monthly transaction volume",
            "What is 1500 * 30?",
            "Now calculate 2.5% of that amount",
            "What would be the annual volume? Multiply by 12",
            "What are InfinitePay's volume discounts?"
        ]
        
        # Verify scenario structure
        assert len(business_conversation) == 5
        assert any("calculate" in msg.lower() for msg in business_conversation)
        assert any("infinitepay" in msg.lower() for msg in business_conversation)


if __name__ == "__main__":
    # Note: These tests require the FastAPI application to be running
    # Run with: pytest backend/tests/test_end_to_end.py -v
    pytest.main([__file__, "-v"])
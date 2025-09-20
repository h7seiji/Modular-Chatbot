"""
Performance tests for agent response times and system throughput.
"""
import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.agents.base import RouterAgent, SpecializedAgent
from backend.models.core import ConversationContext, Message, AgentResponse, AgentDecision


class MockPerformanceAgent(SpecializedAgent):
    """Mock agent with configurable performance characteristics."""
    
    def __init__(self, name: str, base_delay: float = 0.1, keywords: list = None):
        super().__init__(name, keywords or [])
        self.base_delay = base_delay
        self.call_count = 0
        self.total_processing_time = 0.0
    
    def can_handle(self, message: str) -> float:
        """Return confidence based on keywords."""
        if not self.keywords:
            return 0.5
        
        message_lower = message.lower()
        matches = sum(1 for keyword in self.keywords if keyword in message_lower)
        return min(matches / len(self.keywords) * 0.9 + 0.1, 1.0)
    
    async def process(self, message: str, context: ConversationContext) -> AgentResponse:
        """Process with simulated delay."""
        start_time = time.time()
        
        # Simulate processing time
        await asyncio.sleep(self.base_delay)
        
        processing_time = time.time() - start_time
        self.call_count += 1
        self.total_processing_time += processing_time
        
        return AgentResponse(
            content=f"Response from {self.name}",
            source_agent=self.name,
            execution_time=processing_time,
            metadata={
                "call_count": self.call_count,
                "base_delay": self.base_delay
            }
        )


@pytest.fixture
def performance_router():
    """Create router with performance-configured agents."""
    router = RouterAgent()
    
    # Fast agent (simulates simple operations)
    fast_agent = MockPerformanceAgent("FastAgent", base_delay=0.05, keywords=["fast", "quick"])
    
    # Medium agent (simulates moderate complexity)
    medium_agent = MockPerformanceAgent("MediumAgent", base_delay=0.15, keywords=["medium", "normal"])
    
    # Slow agent (simulates complex operations)
    slow_agent = MockPerformanceAgent("SlowAgent", base_delay=0.3, keywords=["slow", "complex"])
    
    router.register_agent(fast_agent)
    router.register_agent(medium_agent)
    router.register_agent(slow_agent)
    
    return router


@pytest.fixture
def conversation_context():
    """Create test conversation context."""
    return ConversationContext(
        conversation_id="perf-test-conv",
        user_id="perf-test-user",
        timestamp=datetime.utcnow(),
        message_history=[
            Message(content="Test message", sender="user", timestamp=datetime.utcnow())
        ]
    )


class TestAgentPerformance:
    """Test individual agent performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_single_agent_response_time(self, conversation_context):
        """Test response time for a single agent call."""
        agent = MockPerformanceAgent("TestAgent", base_delay=0.1)
        
        start_time = time.time()
        response = await agent.process("test message", conversation_context)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Verify response time is within expected range
        assert 0.08 <= total_time <= 0.2  # Allow some variance
        assert response.execution_time > 0
        assert response.source_agent == "TestAgent"
    
    @pytest.mark.asyncio
    async def test_agent_performance_consistency(self, conversation_context):
        """Test that agent performance is consistent across multiple calls."""
        agent = MockPerformanceAgent("ConsistencyAgent", base_delay=0.1)
        
        response_times = []
        num_calls = 10
        
        for _ in range(num_calls):
            start_time = time.time()
            response = await agent.process("test message", conversation_context)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)
        
        # Verify consistency (low standard deviation relative to mean)
        assert std_dev / avg_time < 0.3  # Coefficient of variation < 30%
        assert 0.08 <= avg_time <= 0.2
        
        # Verify agent tracked calls correctly
        assert agent.call_count == num_calls
        assert agent.total_processing_time > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_calls(self, conversation_context):
        """Test agent performance under concurrent load."""
        agent = MockPerformanceAgent("ConcurrentAgent", base_delay=0.1)
        
        num_concurrent = 20
        
        async def make_call():
            start_time = time.time()
            response = await agent.process("concurrent test", conversation_context)
            end_time = time.time()
            return end_time - start_time, response
        
        # Execute concurrent calls
        start_time = time.time()
        tasks = [make_call() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        response_times = [result[0] for result in results]
        responses = [result[1] for result in results]
        
        # Verify all calls completed
        assert len(results) == num_concurrent
        assert all(r.source_agent == "ConcurrentAgent" for r in responses)
        
        # Verify concurrent execution was efficient
        avg_response_time = statistics.mean(response_times)
        assert total_time < num_concurrent * 0.15  # Should be much faster than sequential
        assert 0.08 <= avg_response_time <= 0.2
        
        # Verify agent state is consistent
        assert agent.call_count == num_concurrent


class TestRouterPerformance:
    """Test RouterAgent performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_routing_decision_time(self, performance_router, conversation_context):
        """Test time taken for routing decisions."""
        messages = [
            "This is a fast operation",
            "This is a medium complexity task",
            "This is a slow complex operation"
        ]
        
        routing_times = []
        
        for message in messages:
            start_time = time.time()
            decision = await performance_router.route_message(message, conversation_context)
            end_time = time.time()
            
            routing_time = end_time - start_time
            routing_times.append(routing_time)
            
            # Verify decision is valid
            assert isinstance(decision, AgentDecision)
            assert decision.selected_agent in ["FastAgent", "MediumAgent", "SlowAgent"]
            assert 0.0 <= decision.confidence <= 1.0
        
        # Verify routing is fast
        avg_routing_time = statistics.mean(routing_times)
        max_routing_time = max(routing_times)
        
        assert avg_routing_time < 0.01  # Routing should be very fast
        assert max_routing_time < 0.05  # Even worst case should be quick
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing_time(self, performance_router, conversation_context):
        """Test complete end-to-end processing time."""
        test_cases = [
            ("fast operation", "FastAgent", 0.15),
            ("medium task", "MediumAgent", 0.25),
            ("slow complex operation", "SlowAgent", 0.4)
        ]
        
        for message, expected_agent, max_expected_time in test_cases:
            start_time = time.time()
            response = await performance_router.process(message, conversation_context)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Verify correct agent was selected
            assert response.source_agent == expected_agent
            
            # Verify processing time is within expected bounds
            assert total_time <= max_expected_time
            assert response.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_router_throughput(self, performance_router, conversation_context):
        """Test router throughput under load."""
        num_requests = 50
        messages = [
            "fast operation",
            "medium task", 
            "slow complex operation"
        ] * (num_requests // 3 + 1)
        
        start_time = time.time()
        
        # Process all messages concurrently
        tasks = [
            performance_router.process(message, conversation_context)
            for message in messages[:num_requests]
        ]
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = num_requests / total_time
        
        # Verify all responses are valid
        assert len(responses) == num_requests
        assert all(isinstance(r, AgentResponse) for r in responses)
        
        # Verify reasonable throughput
        assert throughput > 10  # At least 10 requests per second
        
        # Verify response time distribution
        response_times = [r.execution_time for r in responses]
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 0.3  # Average should be reasonable


class TestSystemPerformance:
    """Test overall system performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, performance_router, conversation_context):
        """Test that memory usage remains stable under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process many requests
        num_requests = 100
        for i in range(num_requests):
            message = f"test message {i}"
            await performance_router.process(message, conversation_context)
            
            # Check memory every 20 requests
            if i % 20 == 0:
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (less than 50MB)
                assert memory_growth < 50 * 1024 * 1024
        
        final_memory = process.memory_info().rss
        total_growth = final_memory - initial_memory
        
        # Total memory growth should be reasonable
        assert total_growth < 100 * 1024 * 1024  # Less than 100MB growth
    
    @pytest.mark.asyncio
    async def test_performance_under_different_loads(self, performance_router, conversation_context):
        """Test performance characteristics under different load levels."""
        load_levels = [1, 5, 10, 20, 50]
        performance_metrics = []
        
        for load_level in load_levels:
            # Measure performance at this load level
            start_time = time.time()
            
            tasks = [
                performance_router.process(f"test message {i}", conversation_context)
                for i in range(load_level)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate metrics
            throughput = load_level / total_time
            avg_response_time = statistics.mean(r.execution_time for r in responses)
            
            performance_metrics.append({
                "load_level": load_level,
                "throughput": throughput,
                "avg_response_time": avg_response_time,
                "total_time": total_time
            })
        
        # Verify performance scales reasonably
        for i in range(1, len(performance_metrics)):
            current = performance_metrics[i]
            previous = performance_metrics[i-1]
            
            # Throughput should not degrade significantly
            throughput_ratio = current["throughput"] / previous["throughput"]
            assert throughput_ratio > 0.5  # Should maintain at least 50% of throughput
            
            # Response time should not increase dramatically
            response_time_ratio = current["avg_response_time"] / previous["avg_response_time"]
            assert response_time_ratio < 3.0  # Should not increase more than 3x
    
    def test_synchronous_performance_baseline(self):
        """Test synchronous operations for performance baseline."""
        # Test basic operations that should be very fast
        router = RouterAgent()
        
        # Test agent registration
        start_time = time.time()
        for i in range(100):
            agent = MockPerformanceAgent(f"Agent{i}", base_delay=0.0)
            router.register_agent(agent)
        end_time = time.time()
        
        registration_time = end_time - start_time
        assert registration_time < 0.1  # Should be very fast
        
        # Test can_handle calls
        agent = MockPerformanceAgent("TestAgent", keywords=["test"])
        
        start_time = time.time()
        for i in range(1000):
            confidence = agent.can_handle(f"test message {i}")
            assert 0.0 <= confidence <= 1.0
        end_time = time.time()
        
        can_handle_time = end_time - start_time
        assert can_handle_time < 0.1  # Should be very fast


class TestPerformanceRegression:
    """Test for performance regressions."""
    
    @pytest.mark.asyncio
    async def test_response_time_regression(self, performance_router, conversation_context):
        """Test that response times don't regress beyond acceptable limits."""
        # Define acceptable response time limits for different operations
        performance_limits = {
            "fast": 0.1,      # Fast operations should complete in 100ms
            "medium": 0.2,    # Medium operations should complete in 200ms
            "slow": 0.4       # Slow operations should complete in 400ms
        }
        
        test_cases = [
            ("fast operation", "fast"),
            ("medium complexity task", "medium"),
            ("slow complex operation", "slow")
        ]
        
        for message, operation_type in test_cases:
            # Run multiple iterations to get stable measurements
            response_times = []
            
            for _ in range(10):
                start_time = time.time()
                response = await performance_router.process(message, conversation_context)
                end_time = time.time()
                
                response_times.append(end_time - start_time)
            
            # Calculate 95th percentile response time
            response_times.sort()
            p95_time = response_times[int(0.95 * len(response_times))]
            
            # Verify against performance limit
            limit = performance_limits[operation_type]
            assert p95_time <= limit, \
                f"Performance regression: {operation_type} operation took {p95_time:.3f}s (limit: {limit:.3f}s)"
    
    @pytest.mark.asyncio
    async def test_throughput_regression(self, performance_router, conversation_context):
        """Test that system throughput doesn't regress."""
        # Minimum acceptable throughput (requests per second)
        min_throughput = 20
        
        num_requests = 100
        messages = ["performance test message"] * num_requests
        
        start_time = time.time()
        
        # Process requests in batches to simulate realistic load
        batch_size = 10
        for i in range(0, num_requests, batch_size):
            batch = messages[i:i + batch_size]
            tasks = [
                performance_router.process(message, conversation_context)
                for message in batch
            ]
            await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        throughput = num_requests / total_time
        
        assert throughput >= min_throughput, \
            f"Throughput regression: {throughput:.2f} req/s (minimum: {min_throughput} req/s)"


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics collection."""
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, performance_router, conversation_context):
        """Test that performance metrics are properly collected."""
        # Process several requests
        messages = [
            "fast operation",
            "medium task",
            "slow operation"
        ]
        
        responses = []
        for message in messages:
            response = await performance_router.process(message, conversation_context)
            responses.append(response)
        
        # Verify metrics are collected
        for response in responses:
            assert response.execution_time > 0
            assert "call_count" in response.metadata
            assert response.metadata["call_count"] > 0
        
        # Verify different agents have different performance characteristics
        execution_times = [r.execution_time for r in responses]
        assert len(set(execution_times)) > 1  # Should have different times
    
    def test_performance_profiling_hooks(self):
        """Test that performance profiling hooks work correctly."""
        # This would test integration with profiling tools
        # For now, just verify the structure exists
        
        agent = MockPerformanceAgent("ProfileAgent")
        assert hasattr(agent, 'call_count')
        assert hasattr(agent, 'total_processing_time')
        
        # Verify initial state
        assert agent.call_count == 0
        assert agent.total_processing_time == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
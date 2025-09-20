#!/usr/bin/env python3
"""
Integration test for KnowledgeAgent with Docker environment.

This script tests the KnowledgeAgent functionality in the Docker environment
to ensure it works correctly with the full system.
"""
import os
import sys
import asyncio
import time
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.knowledge_agent import KnowledgeAgent
from models.core import ConversationContext, Message


async def test_knowledge_agent_initialization():
    """Test KnowledgeAgent initialization."""
    print("Testing KnowledgeAgent initialization...")
    
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not found in environment")
            print("   Set OPENAI_API_KEY environment variable to test with real OpenAI API")
            return False
        
        agent = KnowledgeAgent()
        print(f"✅ KnowledgeAgent initialized successfully")
        print(f"   Agent name: {agent.name}")
        print(f"   Keywords count: {len(agent.keywords)}")
        print(f"   Knowledge base URL: {agent.knowledge_base_url}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Failed to initialize KnowledgeAgent: {str(e)}")
        return False


async def test_can_handle_queries(agent):
    """Test the can_handle method with various queries."""
    print("\nTesting can_handle method...")
    
    test_queries = [
        # High confidence queries (InfinitePay specific)
        ("What are InfinitePay card machine fees?", 0.9),
        ("How does the InfinitePay maquininha work?", 0.9),
        ("Tell me about PIX payments on InfinitePay", 0.9),
        
        # Medium confidence queries (general knowledge)
        ("What is payment processing?", 0.6),
        ("How do I set up my account?", 0.6),
        ("Can you help me with integration?", 0.6),
        
        # Low confidence queries (mathematical)
        ("Calculate 5 + 3", 0.3),
        ("What is 10 * 2?", 0.3),
        ("Solve x + 5 = 10", 0.3),
    ]
    
    for query, expected_min_confidence in test_queries:
        confidence = agent.can_handle(query)
        status = "✅" if confidence >= expected_min_confidence else "❌"
        print(f"   {status} '{query}' -> {confidence:.2f} (expected >= {expected_min_confidence})")
    
    print("✅ can_handle method tests completed")


async def test_knowledge_processing(agent):
    """Test processing knowledge queries."""
    print("\nTesting knowledge query processing...")
    
    # Create test conversation context
    context = ConversationContext(
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
    
    test_queries = [
        "What are InfinitePay card machine fees?",
        "How do I set up my InfinitePay account?",
        "Tell me about payment processing",
        "What services does InfinitePay offer?",
    ]
    
    for query in test_queries:
        print(f"\n   Processing: '{query}'")
        start_time = time.time()
        
        try:
            response = await agent.process(query, context)
            execution_time = time.time() - start_time
            
            print(f"   ✅ Response received in {execution_time:.2f}s")
            print(f"      Source agent: {response.source_agent}")
            print(f"      Execution time: {response.execution_time:.3f}s")
            print(f"      Content length: {len(response.content)} characters")
            print(f"      Sources: {len(response.sources) if response.sources else 0}")
            print(f"      Metadata: {response.metadata}")
            
            # Print first 100 characters of response
            content_preview = response.content[:100] + "..." if len(response.content) > 100 else response.content
            print(f"      Preview: {content_preview}")
            
        except Exception as e:
            print(f"   ❌ Error processing query: {str(e)}")
    
    print("\n✅ Knowledge processing tests completed")


async def test_knowledge_base_initialization(agent):
    """Test knowledge base initialization."""
    print("\nTesting knowledge base initialization...")
    
    try:
        # Wait a bit for async initialization to complete
        await asyncio.sleep(2)
        
        if agent.vectorstore is not None:
            print("   ✅ Vector store initialized")
        else:
            print("   ❌ Vector store not initialized")
        
        if agent.scraped_content:
            print(f"   ✅ Scraped content available: {len(agent.scraped_content)} items")
            
            # Show sample content
            for i, content in enumerate(agent.scraped_content[:3]):
                print(f"      Sample {i+1}: {content['title'][:50]}...")
        else:
            print("   ⚠️  No scraped content available (may be using cached data)")
        
        print("✅ Knowledge base initialization test completed")
        
    except Exception as e:
        print(f"❌ Error testing knowledge base: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 Starting KnowledgeAgent Integration Tests")
    print("=" * 50)
    
    # Test initialization
    agent = await test_knowledge_agent_initialization()
    if not agent:
        print("\n❌ Cannot proceed with tests - initialization failed")
        return
    
    # Test can_handle method
    await test_can_handle_queries(agent)
    
    # Test knowledge base initialization
    await test_knowledge_base_initialization(agent)
    
    # Test processing
    await test_knowledge_processing(agent)
    
    print("\n" + "=" * 50)
    print("🎉 KnowledgeAgent Integration Tests Completed")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Verification script to check that the FastAPI implementation is correct.
This script validates the implementation without running the server.
"""
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def verify_imports():
    """Verify that all imports work correctly."""
    print("🔍 Verifying imports...")
    
    try:
        # Test core models
        from models.core import ChatRequest, ChatResponse, ConversationContext, Message, AgentResponse, AgentDecision
        print("✅ Core models imported successfully")
        
        # Test agent base classes
        from agents.base import RouterAgent, SpecializedAgent, BaseAgent
        print("✅ Agent base classes imported successfully")
        
        # Test utilities
        from app.utils.logger import get_logger
        from app.utils.validation import validate_user_id, validate_conversation_id
        print("✅ Utility modules imported successfully")
        
        # Test FastAPI app
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_models():
    """Verify that Pydantic models work correctly."""
    print("\n🔍 Verifying Pydantic models...")
    
    try:
        from models.core import ChatRequest, ChatResponse
        
        # Test ChatRequest validation
        request = ChatRequest(
            message="Hello world",
            user_id="test_user_123",
            conversation_id="test_conv_456"
        )
        print("✅ ChatRequest model validation works")
        
        # Test ChatResponse creation
        response = ChatResponse(
            response="Hello back!",
            source_agent_response="TestAgent (confidence: 0.95)",
            agent_workflow=[
                {"agent": "RouterAgent", "decision": "Routed to TestAgent"},
                {"agent": "TestAgent", "decision": "Processed successfully"}
            ]
        )
        print("✅ ChatResponse model creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False


def verify_agents():
    """Verify that agent classes work correctly."""
    print("\n🔍 Verifying agent classes...")
    
    try:
        from agents.base import RouterAgent
        from models.core import ConversationContext, Message
        from datetime import datetime
        
        # Create router agent
        router = RouterAgent()
        print("✅ RouterAgent created successfully")
        
        # Create mock context
        context = ConversationContext(
            conversation_id="test_conv",
            user_id="test_user",
            message_history=[
                Message(content="Hello", sender="user", timestamp=datetime.utcnow())
            ]
        )
        print("✅ ConversationContext created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent verification error: {e}")
        return False


def verify_fastapi_app():
    """Verify that the FastAPI app is configured correctly."""
    print("\n🔍 Verifying FastAPI app configuration...")
    
    try:
        from app.main import app
        
        # Check that app is a FastAPI instance
        from fastapi import FastAPI
        if not isinstance(app, FastAPI):
            print("❌ App is not a FastAPI instance")
            return False
        
        print("✅ FastAPI app is correctly configured")
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/chat"]
        
        for expected_route in expected_routes:
            if expected_route not in routes:
                print(f"❌ Missing route: {expected_route}")
                return False
        
        print("✅ Required routes are present")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app verification error: {e}")
        return False


def verify_validation():
    """Verify that input validation works correctly."""
    print("\n🔍 Verifying input validation...")
    
    try:
        from app.utils.validation import validate_user_id, validate_conversation_id
        
        # Test valid inputs
        assert validate_user_id("test_user_123") == True
        assert validate_conversation_id("test_conv_456") == True
        print("✅ Valid input validation works")
        
        # Test invalid inputs
        assert validate_user_id("invalid@user") == False
        assert validate_conversation_id("invalid@conv") == False
        print("✅ Invalid input validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation verification error: {e}")
        return False


def main():
    """Run all verification tests."""
    print("🚀 Starting FastAPI implementation verification...\n")
    
    tests = [
        verify_imports,
        verify_models,
        verify_agents,
        verify_fastapi_app,
        verify_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test failed: {test.__name__}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed! The FastAPI implementation is ready.")
        return True
    else:
        print("❌ Some verification tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
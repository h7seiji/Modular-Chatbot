#!/usr/bin/env python3
"""
Simple verification script for MathAgent functionality.
This script can be run to verify that MathAgent is working correctly.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_math_agent_import():
    """Test that MathAgent can be imported successfully."""
    try:
        from agents.math_agent import MathAgent
        print("✅ MathAgent import successful")
        return True
    except Exception as e:
        print(f"❌ MathAgent import failed: {e}")
        return False


def test_math_agent_initialization():
    """Test MathAgent initialization."""
    try:
        # Set a dummy API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"
        
        from agents.math_agent import MathAgent
        agent = MathAgent()
        
        print("✅ MathAgent initialization successful")
        print(f"   Agent name: {agent.name}")
        print(f"   Keywords count: {len(agent.keywords)}")
        print(f"   Sample keywords: {agent.keywords[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ MathAgent initialization failed: {e}")
        return False


def test_math_agent_can_handle():
    """Test MathAgent's can_handle method."""
    try:
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"
        
        from agents.math_agent import MathAgent
        agent = MathAgent()
        
        # Test mathematical queries
        math_queries = [
            ("What is 5 + 3?", "high"),
            ("Calculate 10 * 2", "high"),
            ("How much is 65 x 3.11?", "high"),
            ("Hello, how are you?", "low"),
            ("What are InfinitePay fees?", "low")
        ]
        
        print("✅ Testing MathAgent.can_handle():")
        all_correct = True
        
        for query, expected_level in math_queries:
            confidence = agent.can_handle(query)
            
            if expected_level == "high" and confidence >= 0.7:
                result = "✅"
            elif expected_level == "low" and confidence < 0.5:
                result = "✅"
            else:
                result = "❌"
                all_correct = False
            
            print(f"   {result} '{query}' → {confidence:.2f} (expected {expected_level})")
        
        return all_correct
        
    except Exception as e:
        print(f"❌ MathAgent can_handle test failed: {e}")
        return False


def test_math_agent_expression_detection():
    """Test mathematical expression detection."""
    try:
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"
        
        from agents.math_agent import MathAgent
        agent = MathAgent()
        
        test_cases = [
            ("What is 5 + 3?", ["5 + 3"]),
            ("Calculate 10 * 2.5", ["10 * 2.5"]),
            ("No math here", []),
            ("Solve 7 - 4 and 8 / 2", ["7 - 4", "8 / 2"])
        ]
        
        print("✅ Testing expression detection:")
        all_correct = True
        
        for query, expected_expressions in test_cases:
            detected = agent._detect_mathematical_expressions(query)
            
            # Check if we found the expected expressions
            found_expected = all(
                any(expected in detected_expr for detected_expr in detected)
                for expected in expected_expressions
            )
            
            if (not expected_expressions and not detected) or (expected_expressions and found_expected):
                result = "✅"
            else:
                result = "❌"
                all_correct = False
            
            print(f"   {result} '{query}' → {detected}")
            if expected_expressions:
                print(f"      Expected: {expected_expressions}")
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Expression detection test failed: {e}")
        return False


def test_math_agent_validation():
    """Test input validation."""
    try:
        os.environ["OPENAI_API_KEY"] = "test-key-for-init"
        
        from agents.math_agent import MathAgent
        agent = MathAgent()
        
        safe_expressions = ["5 + 3", "10 * 2.5", "(42 * 2) / 6"]
        dangerous_expressions = ["import os", "exec('print(1)')", "__import__('sys')"]
        
        print("✅ Testing input validation:")
        all_correct = True
        
        for expr in safe_expressions:
            is_safe = agent._validate_mathematical_input(expr)
            result = "✅" if is_safe else "❌"
            if not is_safe:
                all_correct = False
            print(f"   {result} Safe: '{expr}' → {is_safe}")
        
        for expr in dangerous_expressions:
            is_safe = agent._validate_mathematical_input(expr)
            result = "✅" if not is_safe else "❌"
            if is_safe:
                all_correct = False
            print(f"   {result} Dangerous: '{expr}' → {is_safe}")
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("🧮 MathAgent Verification Script")
    print("=" * 50)
    
    # Check environment
    if os.getenv("OPENAI_API_KEY"):
        print("🔑 OpenAI API key found")
    else:
        print("🔑 No OpenAI API key (will use dummy for basic tests)")
    
    print()
    
    # Run tests
    tests = [
        ("Import Test", test_math_agent_import),
        ("Initialization Test", test_math_agent_initialization),
        ("Can Handle Test", test_math_agent_can_handle),
        ("Expression Detection Test", test_math_agent_expression_detection),
        ("Input Validation Test", test_math_agent_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All MathAgent verification tests passed!")
        return True
    else:
        print("⚠️  Some verification tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
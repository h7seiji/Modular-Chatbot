#!/usr/bin/env python3
"""
Test runner for the modular chatbot system.
Runs the essential test suite focusing on core functionality.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run the essential test suite."""
    print("🧪 Running Modular Chatbot Test Suite")
    print("=" * 50)
    
    # Get the backend directory
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests"
    
    # Essential test files
    test_files = [
        "test_router_agent.py",
        "test_math_agent.py", 
        "test_end_to_end.py"
    ]
    
    print("📋 Test Coverage:")
    print("  ✅ RouterAgent decision routing")
    print("  ✅ MathAgent simple expressions")
    print("  ✅ E2E /chat API endpoint")
    print()
    
    # Run each test file
    results = []
    for test_file in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            print(f"🔍 Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(test_path), "-v", "--tb=short"
                ], cwd=backend_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"  ✅ {test_file} - PASSED")
                    results.append(("PASSED", test_file))
                else:
                    print(f"  ❌ {test_file} - FAILED")
                    print(f"     {result.stdout}")
                    if result.stderr:
                        print(f"     {result.stderr}")
                    results.append(("FAILED", test_file))
            except Exception as e:
                print(f"  ❌ {test_file} - ERROR: {e}")
                results.append(("ERROR", test_file))
        else:
            print(f"  ⚠️  {test_file} - NOT FOUND")
            results.append(("NOT_FOUND", test_file))
        print()
    
    # Summary
    print("📊 Test Summary:")
    print("=" * 30)
    
    passed = sum(1 for status, _ in results if status == "PASSED")
    failed = sum(1 for status, _ in results if status == "FAILED")
    errors = sum(1 for status, _ in results if status == "ERROR")
    not_found = sum(1 for status, _ in results if status == "NOT_FOUND")
    
    for status, test_file in results:
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "ERROR": "⚠️",
            "NOT_FOUND": "❓"
        }.get(status, "❓")
        print(f"  {status_icon} {test_file}: {status}")
    
    print()
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Not Found: {not_found}")
    
    if failed > 0 or errors > 0:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1
    elif not_found > 0:
        print("\n⚠️  Some test files were not found.")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0

def run_specific_test(test_name):
    """Run a specific test file."""
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests"
    
    test_file = tests_dir / f"test_{test_name}.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print(f"🔍 Running {test_file.name}...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), "-v", "--tb=short"
        ], cwd=backend_dir)
        
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        # Run all tests
        return run_tests()

if __name__ == "__main__":
    sys.exit(main())
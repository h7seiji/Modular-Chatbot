"""
Comprehensive test runner for the modular chatbot backend.
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, description, capture_output=False):
    """Run a command and handle output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            success = result.returncode == 0
        else:
            result = subprocess.run(
                command, 
                shell=True,
                cwd=Path(__file__).parent
            )
            success = result.returncode == 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {description} (took {duration:.2f}s)")
        
        return success
        
    except Exception as e:
        print(f"❌ ERROR running {description}: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "fastapi",
        "uvicorn",
        "pydantic",
        "redis"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: uv add " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed")
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd_parts = ["python", "-m", "pytest", "tests/"]
    
    # Add specific unit test files
    unit_test_files = [
        "tests/test_models.py",
        "tests/test_validation.py", 
        "tests/test_logger.py",
        "tests/test_math_agent.py",
        "tests/test_knowledge_agent.py",
        "tests/test_router_agent.py",
        "tests/test_security.py"
    ]
    
    cmd_parts.extend(unit_test_files)
    
    if verbose:
        cmd_parts.append("-v")
    
    if coverage:
        cmd_parts.extend(["--cov=app", "--cov=agents", "--cov=models", "--cov=services"])
        cmd_parts.extend(["--cov-report=term-missing", "--cov-report=html"])
    
    cmd_parts.extend(["-m", "unit"])
    
    command = " ".join(cmd_parts)
    return run_command(command, "Unit Tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd_parts = ["python", "-m", "pytest", "tests/test_integration.py"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "integration"])
    
    command = " ".join(cmd_parts)
    return run_command(command, "Integration Tests")


def run_performance_tests(verbose=False):
    """Run performance tests."""
    cmd_parts = ["python", "-m", "pytest", "tests/test_performance.py"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "performance"])
    
    command = " ".join(cmd_parts)
    return run_command(command, "Performance Tests")


def run_security_tests(verbose=False):
    """Run security tests."""
    cmd_parts = ["python", "-m", "pytest", "tests/test_security.py"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "security"])
    
    command = " ".join(cmd_parts)
    return run_command(command, "Security Tests")


def run_end_to_end_tests(verbose=False):
    """Run end-to-end tests."""
    print("\n⚠️  End-to-end tests require the FastAPI application to be running")
    print("Start the application with: uvicorn app.main:app --reload")
    
    response = input("Is the application running? (y/N): ").lower().strip()
    if response != 'y':
        print("Skipping end-to-end tests")
        return True
    
    cmd_parts = ["python", "-m", "pytest", "tests/test_end_to_end.py"]
    
    if verbose:
        cmd_parts.append("-v")
    
    cmd_parts.extend(["-m", "integration"])
    
    command = " ".join(cmd_parts)
    return run_command(command, "End-to-End Tests")


def run_linting():
    """Run code linting with ruff."""
    commands = [
        ("python -m ruff check .", "Ruff Linting"),
        ("python -m ruff format --check .", "Ruff Format Check")
    ]
    
    results = []
    for command, description in commands:
        results.append(run_command(command, description, capture_output=True))
    
    return all(results)


def run_type_checking():
    """Run type checking with ty."""
    command = "python -m ty ."
    return run_command(command, "Type Checking", capture_output=True)


def generate_coverage_report():
    """Generate detailed coverage report."""
    commands = [
        ("python -m pytest --cov=app --cov=agents --cov=models --cov=services --cov-report=html --cov-report=xml tests/", "Coverage Report Generation")
    ]
    
    for command, description in commands:
        success = run_command(command, description, capture_output=True)
        if success:
            print("📊 Coverage report generated in htmlcov/index.html")
        return success


def run_docker_tests():
    """Run tests in Docker environment."""
    print("\n🐳 Running tests in Docker environment...")
    
    # Check if Docker is available
    docker_check = subprocess.run(["docker", "--version"], capture_output=True)
    if docker_check.returncode != 0:
        print("❌ Docker is not available")
        return False
    
    # Build test image
    build_cmd = "docker build -t modular-chatbot-test -f Dockerfile.test ."
    if not run_command(build_cmd, "Building Docker Test Image"):
        return False
    
    # Run tests in container
    test_cmd = "docker run --rm modular-chatbot-test"
    return run_command(test_cmd, "Running Tests in Docker")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for modular chatbot backend")
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--type-check", action="store_true", help="Run type checking only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--docker", action="store_true", help="Run tests in Docker")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    
    print("🧪 Modular Chatbot Backend Test Runner")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    results = []
    
    # Determine what to run
    if args.all or not any([args.unit, args.integration, args.performance, args.security, args.e2e, args.lint, args.type_check, args.coverage, args.docker]):
        # Run everything if no specific option is chosen
        run_all = True
    else:
        run_all = False
    
    # Run linting
    if args.lint or run_all:
        results.append(("Linting", run_linting()))
    
    # Run type checking
    if args.type_check or run_all:
        results.append(("Type Checking", run_type_checking()))
    
    # Run unit tests
    if args.unit or run_all:
        results.append(("Unit Tests", run_unit_tests(args.verbose, args.coverage or run_all)))
    
    # Run integration tests
    if args.integration or run_all:
        results.append(("Integration Tests", run_integration_tests(args.verbose)))
    
    # Run performance tests (skip if --fast)
    if (args.performance or run_all) and not args.fast:
        results.append(("Performance Tests", run_performance_tests(args.verbose)))
    
    # Run security tests
    if args.security or run_all:
        results.append(("Security Tests", run_security_tests(args.verbose)))
    
    # Run end-to-end tests (skip if --fast)
    if (args.e2e or run_all) and not args.fast:
        results.append(("End-to-End Tests", run_end_to_end_tests(args.verbose)))
    
    # Generate coverage report
    if args.coverage:
        results.append(("Coverage Report", generate_coverage_report()))
    
    # Run Docker tests
    if args.docker:
        results.append(("Docker Tests", run_docker_tests()))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}")
    
    if failed_tests > 0:
        print(f"\n❌ {failed_tests} test suite(s) failed")
        sys.exit(1)
    else:
        print(f"\n✅ All {passed_tests} test suite(s) passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
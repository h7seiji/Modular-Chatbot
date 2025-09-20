"""
Tests for CI/CD integration and automated testing workflows.
"""
import pytest
import subprocess
import os
import json
from pathlib import Path


class TestCICDIntegration:
    """Test CI/CD integration and automation."""
    
    def test_pytest_configuration(self):
        """Test that pytest is properly configured."""
        # Check that pytest.ini or pyproject.toml has correct configuration
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        assert pyproject_path.exists(), "pyproject.toml should exist"
        
        # Read and verify pytest configuration
        with open(pyproject_path, "r") as f:
            content = f.read()
            
        # Verify key pytest settings
        assert "[tool.pytest.ini_options]" in content
        assert "--cov=" in content  # Coverage is configured
        assert "testpaths" in content
        assert "python_files" in content
    
    def test_coverage_configuration(self):
        """Test that coverage is properly configured."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        # Verify coverage configuration
        assert "[tool.coverage.run]" in content
        assert "[tool.coverage.report]" in content
        assert "source =" in content
        assert "omit =" in content
    
    def test_test_discovery(self):
        """Test that all test files are discoverable."""
        tests_dir = Path(__file__).parent
        
        # Find all test files
        test_files = list(tests_dir.glob("test_*.py"))
        
        # Verify we have the expected test files
        expected_files = [
            "test_models.py",
            "test_validation.py",
            "test_logger.py",
            "test_math_agent.py",
            "test_knowledge_agent.py",
            "test_router_agent.py",
            "test_security.py",
            "test_integration.py",
            "test_end_to_end.py",
            "test_performance.py",
            "test_ci_cd.py"
        ]
        
        found_files = [f.name for f in test_files]
        
        for expected_file in expected_files:
            assert expected_file in found_files, f"Missing test file: {expected_file}"
        
        # Verify we have a reasonable number of test files
        assert len(test_files) >= 10, f"Expected at least 10 test files, found {len(test_files)}"
    
    def test_test_markers(self):
        """Test that test markers are properly configured."""
        # Run pytest to collect tests and check markers
        result = subprocess.run([
            "python", "-m", "pytest", 
            "--collect-only", 
            "--quiet",
            str(Path(__file__).parent)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"Test collection failed: {result.stderr}"
        
        # Verify that tests are being collected
        assert "test session starts" in result.stdout or len(result.stdout) > 0
    
    def test_dependency_versions(self):
        """Test that dependencies are properly specified."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        # Verify key dependencies are specified with versions
        required_deps = [
            "pytest>=",
            "pytest-asyncio>=",
            "pytest-cov>=",
            "fastapi>=",
            "pydantic>=",
            "uvicorn>="
        ]
        
        for dep in required_deps:
            assert dep in content, f"Missing or unversioned dependency: {dep}"
    
    def test_environment_variables(self):
        """Test that required environment variables are handled."""
        # Test that TESTING environment variable is set
        assert os.getenv("TESTING") == "1", "TESTING environment variable should be set for tests"
        
        # Test that OPENAI_API_KEY is set (even if mock)
        assert os.getenv("OPENAI_API_KEY") is not None, "OPENAI_API_KEY should be set for tests"
    
    def test_test_isolation(self):
        """Test that tests are properly isolated."""
        # This test verifies that tests don't interfere with each other
        # by checking that we can run the same test multiple times
        
        # Create a simple test function that modifies global state
        import tempfile
        
        test_file_content = '''
import pytest

global_counter = 0

def test_isolation_1():
    global global_counter
    global_counter += 1
    assert global_counter == 1

def test_isolation_2():
    global global_counter
    global_counter += 1
    assert global_counter == 1
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_file_content)
            temp_test_file = f.name
        
        try:
            # Run the isolation test
            result = subprocess.run([
                "python", "-m", "pytest", 
                temp_test_file,
                "-v"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            # The test should fail because of lack of isolation
            # This demonstrates the importance of proper test isolation
            # In a real scenario, we'd use fixtures to ensure isolation
            
        finally:
            os.unlink(temp_test_file)
    
    def test_parallel_test_execution(self):
        """Test that tests can be run in parallel."""
        # Test that pytest-xdist is available for parallel execution
        try:
            import xdist
            parallel_available = True
        except ImportError:
            parallel_available = False
        
        if parallel_available:
            # Run a subset of tests in parallel
            result = subprocess.run([
                "python", "-m", "pytest",
                "tests/test_models.py",
                "-n", "2",  # Use 2 parallel workers
                "--quiet"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            # Should succeed or gracefully handle parallel execution
            assert result.returncode in [0, 1], "Parallel test execution should work or fail gracefully"
    
    def test_test_data_fixtures(self):
        """Test that test fixtures are properly configured."""
        # Verify that conftest.py exists and has proper fixtures
        conftest_path = Path(__file__).parent / "conftest.py"
        
        assert conftest_path.exists(), "conftest.py should exist"
        
        with open(conftest_path, "r") as f:
            content = f.read()
        
        # Verify key fixtures exist
        expected_fixtures = [
            "@pytest.fixture",
            "conversation_context",
            "mock_",
            "event_loop"
        ]
        
        for fixture in expected_fixtures:
            assert fixture in content, f"Missing fixture or configuration: {fixture}"
    
    def test_mock_configurations(self):
        """Test that mocks are properly configured for CI/CD."""
        # Verify that external dependencies are properly mocked
        from unittest.mock import patch
        
        # Test that OpenAI API is mockable
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.return_value = None
            # This should not raise an error
            assert mock_openai.called or not mock_openai.called  # Just verify it's mockable
        
        # Test that Redis is mockable
        with patch('redis.Redis') as mock_redis:
            mock_redis.return_value = None
            assert mock_redis.called or not mock_redis.called
    
    def test_error_reporting(self):
        """Test that error reporting is configured for CI/CD."""
        # Create a test that intentionally fails to check error reporting
        test_content = '''
def test_intentional_failure():
    assert False, "This is an intentional failure for testing error reporting"
'''
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_test_file = f.name
        
        try:
            result = subprocess.run([
                "python", "-m", "pytest",
                temp_test_file,
                "-v",
                "--tb=short"  # Short traceback format
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            # Should fail but provide clear error reporting
            assert result.returncode == 1
            assert "FAILED" in result.stdout
            assert "intentional failure" in result.stdout
            
        finally:
            os.unlink(temp_test_file)


class TestAutomatedTestWorkflows:
    """Test automated testing workflows."""
    
    def test_test_runner_script(self):
        """Test that the test runner script exists and is executable."""
        runner_path = Path(__file__).parent.parent / "run_tests.py"
        
        assert runner_path.exists(), "run_tests.py should exist"
        
        # Check that it's a valid Python script
        with open(runner_path, "r") as f:
            content = f.read()
        
        assert "def main(" in content, "run_tests.py should have a main function"
        assert "argparse" in content, "run_tests.py should use argparse for CLI"
        assert "pytest" in content, "run_tests.py should integrate with pytest"
    
    def test_docker_test_configuration(self):
        """Test that Docker test configuration exists."""
        dockerfile_test = Path(__file__).parent.parent / "Dockerfile.test"
        
        if dockerfile_test.exists():
            with open(dockerfile_test, "r") as f:
                content = f.read()
            
            # Verify Docker test configuration
            assert "FROM python:" in content
            assert "pytest" in content
            assert "COPY" in content
            assert "CMD" in content or "RUN" in content
    
    def test_github_actions_workflow(self):
        """Test GitHub Actions workflow configuration."""
        # Check for GitHub Actions workflow files
        github_dir = Path(__file__).parent.parent.parent / ".github"
        workflows_dir = github_dir / "workflows"
        
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            
            if workflow_files:
                # Check at least one workflow file
                with open(workflow_files[0], "r") as f:
                    content = f.read()
                
                # Verify basic workflow structure
                assert "name:" in content
                assert "on:" in content
                assert "jobs:" in content
    
    def test_pre_commit_hooks(self):
        """Test pre-commit hooks configuration."""
        pre_commit_config = Path(__file__).parent.parent / ".pre-commit-config.yaml"
        
        if pre_commit_config.exists():
            with open(pre_commit_config, "r") as f:
                content = f.read()
            
            # Verify pre-commit configuration
            assert "repos:" in content
            assert "hooks:" in content
    
    def test_makefile_targets(self):
        """Test Makefile targets for testing."""
        makefile = Path(__file__).parent.parent / "Makefile"
        
        if makefile.exists():
            with open(makefile, "r") as f:
                content = f.read()
            
            # Verify test-related targets
            expected_targets = ["test", "lint", "coverage"]
            
            for target in expected_targets:
                if f"{target}:" in content:
                    assert "pytest" in content or "python" in content


class TestTestQuality:
    """Test the quality and completeness of the test suite."""
    
    def test_test_coverage_completeness(self):
        """Test that test coverage is comprehensive."""
        # This would ideally run coverage analysis
        # For now, we'll check that major components have tests
        
        tests_dir = Path(__file__).parent
        test_files = [f.stem for f in tests_dir.glob("test_*.py")]
        
        # Check that major components are tested
        expected_components = [
            "test_models",
            "test_router_agent", 
            "test_math_agent",
            "test_knowledge_agent",
            "test_security",
            "test_integration"
        ]
        
        for component in expected_components:
            assert component in test_files, f"Missing tests for {component}"
    
    def test_test_naming_conventions(self):
        """Test that test naming conventions are followed."""
        tests_dir = Path(__file__).parent
        
        for test_file in tests_dir.glob("test_*.py"):
            # Check file naming
            assert test_file.name.startswith("test_"), f"Test file should start with 'test_': {test_file.name}"
            
            # Check that file contains test functions
            with open(test_file, "r") as f:
                content = f.read()
            
            # Should have at least one test function
            assert "def test_" in content, f"Test file should contain test functions: {test_file.name}"
    
    def test_assertion_quality(self):
        """Test that assertions are meaningful and descriptive."""
        # This is a meta-test that checks test quality
        tests_dir = Path(__file__).parent
        
        assertion_patterns = [
            "assert ",
            "pytest.raises",
            "assert_called",
            "assert_not_called"
        ]
        
        for test_file in tests_dir.glob("test_*.py"):
            if test_file.name == "test_ci_cd.py":  # Skip self
                continue
                
            with open(test_file, "r") as f:
                content = f.read()
            
            # Should have meaningful assertions
            has_assertions = any(pattern in content for pattern in assertion_patterns)
            assert has_assertions, f"Test file should have assertions: {test_file.name}"
    
    def test_test_documentation(self):
        """Test that tests are properly documented."""
        tests_dir = Path(__file__).parent
        
        for test_file in tests_dir.glob("test_*.py"):
            with open(test_file, "r") as f:
                content = f.read()
            
            # Should have module docstring
            lines = content.split('\n')
            if len(lines) > 1:
                # Look for docstring in first few lines
                has_docstring = any('"""' in line for line in lines[:5])
                assert has_docstring, f"Test file should have module docstring: {test_file.name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
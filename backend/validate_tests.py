"""
Validate test structure and configuration without running tests.
"""
import os
import sys
from pathlib import Path
import ast
import importlib.util


def validate_test_file(test_file_path):
    """Validate a single test file."""
    print(f"Validating {test_file_path.name}...")
    
    try:
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        # Parse the AST to check for syntax errors
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"  ❌ Syntax error: {e}")
            return False
        
        # Check for test functions
        test_functions = []
        test_classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_functions.append(node.name)
            elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                test_classes.append(node.name)
        
        if not test_functions and not test_classes:
            print(f"  ⚠️  No test functions or classes found")
            return False
        
        print(f"  ✅ Found {len(test_functions)} test functions and {len(test_classes)} test classes")
        
        # Check for imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Check for pytest import
        has_pytest = any('pytest' in imp for imp in imports)
        if not has_pytest:
            print(f"  ⚠️  No pytest import found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error validating file: {e}")
        return False


def validate_test_structure():
    """Validate overall test structure."""
    print("Validating test structure...")
    
    tests_dir = Path(__file__).parent / "tests"
    
    if not tests_dir.exists():
        print("❌ Tests directory does not exist")
        return False
    
    # Check for conftest.py
    conftest_path = tests_dir / "conftest.py"
    if conftest_path.exists():
        print("✅ conftest.py found")
    else:
        print("⚠️  conftest.py not found")
    
    # Find all test files
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print("❌ No test files found")
        return False
    
    print(f"✅ Found {len(test_files)} test files")
    
    # Validate each test file
    valid_files = 0
    for test_file in test_files:
        if validate_test_file(test_file):
            valid_files += 1
    
    print(f"\n📊 Summary: {valid_files}/{len(test_files)} test files are valid")
    
    return valid_files == len(test_files)


def validate_dependencies():
    """Validate that test dependencies are available."""
    print("Validating test dependencies...")
    
    required_modules = [
        'pytest',
        'unittest.mock',
        'asyncio',
        'datetime',
        'pathlib'
    ]
    
    missing_modules = []
    
    for module_name in required_modules:
        try:
            if '.' in module_name:
                # Handle submodules
                parent_module = module_name.split('.')[0]
                importlib.import_module(parent_module)
            else:
                importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError:
            print(f"  ❌ {module_name}")
            missing_modules.append(module_name)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        return False
    
    print("✅ All required modules are available")
    return True


def validate_project_structure():
    """Validate project structure for testing."""
    print("Validating project structure...")
    
    backend_dir = Path(__file__).parent
    
    # Check for key directories
    required_dirs = [
        "app",
        "agents", 
        "models",
        "services",
        "tests"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = backend_dir / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/")
            missing_dirs.append(dir_name)
    
    # Check for key files
    required_files = [
        "pyproject.toml",
        "app/main.py",
        "agents/base.py",
        "models/core.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = backend_dir / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name}")
            missing_files.append(file_name)
    
    if missing_dirs or missing_files:
        print(f"\n❌ Missing directories: {missing_dirs}")
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Project structure is valid")
    return True


def validate_pytest_config():
    """Validate pytest configuration."""
    print("Validating pytest configuration...")
    
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    # Check for pytest configuration
    if "[tool.pytest.ini_options]" not in content:
        print("❌ pytest configuration not found in pyproject.toml")
        return False
    
    print("✅ pytest configuration found")
    
    # Check for coverage configuration
    if "[tool.coverage" in content:
        print("✅ Coverage configuration found")
    else:
        print("⚠️  Coverage configuration not found")
    
    return True


def main():
    """Main validation function."""
    print("🧪 Test Suite Validation")
    print("=" * 50)
    
    validations = [
        ("Project Structure", validate_project_structure),
        ("Test Dependencies", validate_dependencies),
        ("Pytest Configuration", validate_pytest_config),
        ("Test Structure", validate_test_structure)
    ]
    
    results = []
    
    for name, validation_func in validations:
        print(f"\n{name}:")
        print("-" * 30)
        result = validation_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All validations passed! Test suite is ready.")
        return 0
    else:
        print(f"\n❌ {total - passed} validation(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Verification script for KnowledgeAgent implementation.

This script verifies that the KnowledgeAgent is properly implemented and integrated
with the modular chatbot system.
"""
import os
import sys
import importlib.util
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} missing: {file_path}")
        return False


def check_import(module_name: str, description: str) -> bool:
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description} imports successfully")
        return True
    except ImportError as e:
        print(f"❌ {description} import failed: {str(e)}")
        return False


def check_class_methods(module_name: str, class_name: str, required_methods: list) -> bool:
    """Check if a class has required methods."""
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(cls, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ {class_name} missing methods: {missing_methods}")
            return False
        else:
            print(f"✅ {class_name} has all required methods")
            return True
            
    except Exception as e:
        print(f"❌ Error checking {class_name}: {str(e)}")
        return False


def main():
    """Main verification function."""
    print("🔍 Verifying KnowledgeAgent Implementation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check required files
    required_files = [
        ("backend/agents/knowledge_agent.py", "KnowledgeAgent implementation"),
        ("backend/tests/test_knowledge_agent.py", "KnowledgeAgent unit tests"),
        ("backend/test_knowledge_agent_integration.py", "KnowledgeAgent integration test"),
        ("test_knowledge_agent_docker.py", "Docker integration test (Python)"),
        ("test_knowledge_agent_docker.ps1", "Docker integration test (PowerShell)"),
    ]
    
    print("\n📁 Checking required files...")
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Check imports
    print("\n📦 Checking imports...")
    import_checks = [
        ("backend.agents.knowledge_agent", "KnowledgeAgent module"),
        ("backend.models.core", "Core models"),
        ("backend.agents.base", "Base agent classes"),
    ]
    
    for module_name, description in import_checks:
        if not check_import(module_name, description):
            all_checks_passed = False
    
    # Check KnowledgeAgent class structure
    print("\n🏗️  Checking KnowledgeAgent class structure...")
    required_methods = [
        "__init__",
        "can_handle",
        "process",
        "_initialize_knowledge_base",
        "_scrape_infinitepay_content",
        "_retrieve_relevant_content",
        "_generate_response_with_context",
    ]
    
    if not check_class_methods("backend.agents.knowledge_agent", "KnowledgeAgent", required_methods):
        all_checks_passed = False
    
    # Check dependencies in pyproject.toml
    print("\n📋 Checking dependencies...")
    try:
        with open("backend/pyproject.toml", "r") as f:
            content = f.read()
            
        required_deps = [
            "langchain",
            "chromadb", 
            "beautifulsoup4",
            "openai",
            "requests"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep not in content:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing dependencies in pyproject.toml: {missing_deps}")
            all_checks_passed = False
        else:
            print("✅ All required dependencies found in pyproject.toml")
            
    except Exception as e:
        print(f"❌ Error checking dependencies: {str(e)}")
        all_checks_passed = False
    
    # Check integration with main app
    print("\n🔗 Checking integration with main app...")
    try:
        with open("backend/app/main.py", "r") as f:
            content = f.read()
            
        if "from agents.knowledge_agent import KnowledgeAgent" in content:
            print("✅ KnowledgeAgent imported in main.py")
        else:
            print("❌ KnowledgeAgent not imported in main.py")
            all_checks_passed = False
            
        if "KnowledgeAgent()" in content:
            print("✅ KnowledgeAgent instantiated in main.py")
        else:
            print("❌ KnowledgeAgent not instantiated in main.py")
            all_checks_passed = False
            
    except Exception as e:
        print(f"❌ Error checking main.py integration: {str(e)}")
        all_checks_passed = False
    
    # Check agents __init__.py
    print("\n📦 Checking agents package...")
    try:
        with open("backend/agents/__init__.py", "r") as f:
            content = f.read()
            
        if "KnowledgeAgent" in content:
            print("✅ KnowledgeAgent exported from agents package")
        else:
            print("❌ KnowledgeAgent not exported from agents package")
            all_checks_passed = False
            
    except Exception as e:
        print(f"❌ Error checking agents/__init__.py: {str(e)}")
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All verification checks passed!")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Run unit tests: pytest backend/tests/test_knowledge_agent.py")
        print("3. Run integration test: python backend/test_knowledge_agent_integration.py")
        print("4. Test with Docker: python test_knowledge_agent_docker.py")
        return True
    else:
        print("❌ Some verification checks failed!")
        print("Please fix the issues above before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
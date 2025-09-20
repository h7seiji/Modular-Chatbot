#!/usr/bin/env python3
"""
Script to verify the modernized backend setup.
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (missing)")
        return False


def verify_setup():
    """Verify that all modernization components are in place."""
    print("🔍 Verifying backend modernization setup...\n")
    
    all_good = True
    
    # Check core configuration files
    all_good &= check_file_exists("pyproject.toml", "Project configuration")
    all_good &= check_file_exists(".pre-commit-config.yaml", "Pre-commit configuration")
    all_good &= check_file_exists("Makefile", "Development commands")
    all_good &= check_file_exists("README.md", "Documentation")
    
    # Check if pyproject.toml has the right content
    if Path("pyproject.toml").exists():
        with open("pyproject.toml", "r") as f:
            content = f.read()
            if "ruff" in content:
                print("✅ Ruff configuration found in pyproject.toml")
            else:
                print("❌ Ruff configuration missing in pyproject.toml")
                all_good = False
                
            if "ty" in content:
                print("✅ Ty configuration found in pyproject.toml")
            else:
                print("❌ Ty configuration missing in pyproject.toml")
                all_good = False
                
            if "pytest" in content:
                print("✅ Pytest configuration found in pyproject.toml")
            else:
                print("❌ Pytest configuration missing in pyproject.toml")
                all_good = False
    
    # Check if old requirements.txt still exists
    if Path("requirements.txt").exists():
        print("⚠️  requirements.txt still exists (can be removed after verification)")
    else:
        print("✅ requirements.txt has been removed")
    
    print(f"\n{'✅ Setup verification complete!' if all_good else '❌ Setup verification failed!'}")
    
    if all_good:
        print("\nNext steps:")
        print("1. Install uv if not already installed:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("2. Run setup: python setup_venv.py")
        print("3. Or manually: uv sync --all-extras")
        print("4. Install pre-commit: uv run pre-commit install")
        print("5. Run tests: make test")
    
    return all_good


if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
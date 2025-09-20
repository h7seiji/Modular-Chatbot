#!/usr/bin/env python3
"""
Script to set up Python environment using uv for the backend.
This script is now simplified since dependencies are managed via pyproject.toml.
"""
import subprocess
import sys
import os


def setup_uv_environment():
    """Set up Python environment using uv and install dependencies."""
    try:
        # Check if uv is installed
        print("Checking if uv is installed...")
        try:
            result = subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
            print(f"uv is installed: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("uv is not installed. Please install uv first:")
            print("Visit: https://docs.astral.sh/uv/getting-started/installation/")
            sys.exit(1)
        
        # Check if pyproject.toml exists
        if not os.path.exists("pyproject.toml"):
            print("Error: pyproject.toml not found!")
            print("This script should be run from the backend directory.")
            sys.exit(1)
        
        # Install dependencies from pyproject.toml
        print("Installing dependencies with uv...")
        subprocess.run(["uv", "sync", "--all-extras"], check=True)
        
        # Install pre-commit hooks
        print("Installing pre-commit hooks...")
        subprocess.run(["uv", "run", "pre-commit", "install"], check=True)
        
        print("\n✅ uv environment setup complete!")
        print("\nAvailable commands:")
        print("  make help           - Show all available make commands")
        print("  make install-dev    - Install all dependencies")
        print("  make test           - Run tests")
        print("  make lint           - Run linting")
        print("  make format         - Format code")
        print("  make type-check     - Run type checking")
        print("  make run            - Start development server")
        print("  uv run <command>    - Run any command in the uv environment")
        
        # Check if requirements.txt still exists and suggest removal
        if os.path.exists("requirements.txt"):
            print("\n⚠️  Note: requirements.txt is still present.")
            print("   Dependencies are now managed in pyproject.toml.")
            print("   You can safely remove requirements.txt after verifying the migration.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up uv environment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_uv_environment()
"""
Logging configuration for different environments.

This module provides environment-specific logging configurations
for development, testing, and production environments.
"""

import logging
import os
from typing import Dict, Any

from .logger import configure_logging


def get_log_level() -> str:
    """Get log level from environment variable."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_environment() -> str:
    """Get current environment from environment variable."""
    return os.getenv("ENVIRONMENT", "development").lower()


def setup_development_logging():
    """Configure logging for development environment."""
    configure_logging(level="DEBUG", format_type="json")
    
    # Enable more verbose logging for development
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)


def setup_production_logging():
    """Configure logging for production environment."""
    configure_logging(level="INFO", format_type="json")
    
    # Reduce noise in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def setup_testing_logging():
    """Configure logging for testing environment."""
    configure_logging(level="WARNING", format_type="json")
    
    # Minimize logging during tests
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("fastapi").setLevel(logging.CRITICAL)


def initialize_logging():
    """Initialize logging based on current environment."""
    environment = get_environment()
    
    if environment == "production":
        setup_production_logging()
    elif environment == "testing":
        setup_testing_logging()
    else:
        setup_development_logging()
    
    # Log initialization
    from .logger import main_logger
    main_logger.info(
        f"Logging initialized for {environment} environment",
        metadata={"environment": environment, "log_level": get_log_level()}
    )


# Environment-specific configurations
LOGGING_CONFIGS: Dict[str, Dict[str, Any]] = {
    "development": {
        "level": "DEBUG",
        "format": "json",
        "enable_console": True,
        "enable_file": False,
    },
    "production": {
        "level": "INFO",
        "format": "json",
        "enable_console": True,
        "enable_file": True,
        "file_path": "/var/log/chatbot/app.log",
    },
    "testing": {
        "level": "WARNING",
        "format": "json",
        "enable_console": False,
        "enable_file": False,
    },
}


def get_logging_config(environment: str = None) -> Dict[str, Any]:
    """Get logging configuration for specified environment."""
    if environment is None:
        environment = get_environment()
    
    return LOGGING_CONFIGS.get(environment, LOGGING_CONFIGS["development"])
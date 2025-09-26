"""
Google credentials utility for Cloud Run deployment.
This module handles Google Cloud credentials when deployed to Cloud Run.
"""
import os
import tempfile
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)


def setup_google_credentials() -> str | None:
    """
    Set up Google Cloud credentials from environment variable or copied file.

    First tries to use the copied credentials file at /home/google-credentials.json.
    If that doesn't exist, falls back to creating a temporary file from
    GOOGLE_APPLICATION_CREDENTIALS_CONTENT environment variable.

    Returns:
        Path to the credentials file if successful, None otherwise
    """
    # First, check if the copied credentials file exists
    copied_credentials_path = Path("/home/google-credentials.json")
    if copied_credentials_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(copied_credentials_path)
        logger.info(f"Using copied credentials file: {copied_credentials_path}")
        return str(copied_credentials_path)

    # If copied file doesn't exist, check if credentials content is provided in environment variable
    credentials_content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

    if not credentials_content:
        # Check if traditional credentials file path is set
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and Path(credentials_path).exists():
            logger.info(f"Using existing credentials file: {credentials_path}")
            return credentials_path

        logger.warning("No Google Cloud credentials found in environment variables")
        return None

    try:
        # Create a temporary file for the credentials
        temp_dir = Path(tempfile.gettempdir())
        credentials_file = temp_dir / "google-credentials.json"

        # Write the credentials content to the file
        credentials_file.write_text(credentials_content)

        # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_file)

        logger.info(f"Google Cloud credentials set up at: {credentials_file}")
        return str(credentials_file)

    except Exception as e:
        logger.error(f"Failed to set up Google Cloud credentials: {e}")
        return None


def get_credentials_path() -> str | None:
    """
    Get the path to the Google Cloud credentials file.

    Returns:
        Path to the credentials file if available, None otherwise
    """
    # First try to get from environment variable (set by setup_google_credentials)
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path and Path(credentials_path).exists():
        return credentials_path

    # If not set, try to set it up from content
    return setup_google_credentials()

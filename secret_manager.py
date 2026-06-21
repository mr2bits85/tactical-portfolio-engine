"""
Utility for loading secrets from Google Secret Manager with fallback to environment variables.
"""
import os
import logging
from typing import Optional

# Try to import Google Secret Manager client; if not available, we'll rely on env vars.
try:
    from google.cloud import secretmanager
    from google.api_core import exceptions
    _secret_manager_available = True
except ImportError:
    _secret_manager_available = False

logger = logging.getLogger(__name__)


class SecretManager:
    """
    A utility class to access secrets from Google Secret Manager.
    Falls back to environment variables if Secret Manager is unavailable or if running locally.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Secret Manager client.

        Args:
            project_id: Google Cloud Project ID. If not provided, it will be read from
                        the GOOGLE_CLOUD_PROJECT environment variable.
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._client = None
        if _secret_manager_available and self.project_id:
            try:
                self._client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized.")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Secret Manager client: {e}. Falling back to environment variables."
                )
                self._client = None
        else:
            if not _secret_manager_available:
                logger.warning(
                    "Google Secret Manager library not installed. Falling back to environment variables."
                )
            if not self.project_id:
                logger.warning(
                    "GOOGLE_CLOUD_PROJECT environment variable not set. Falling back to environment variables."
                )

    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """
        Retrieve a secret from Secret Manager or fallback to environment variable.

        Args:
            secret_name: The name of the secret.
            version: The version of the secret (default: "latest").

        Returns:
            The secret value as a string, or None if not found.
        """
        # First, try to get from environment variable (for local development or fallback)
        env_var = os.getenv(secret_name)
        if env_var is not None:
            logger.debug(f"Retrieved secret '{secret_name}' from environment variable.")
            return env_var

        # If Secret Manager client is not available, return None (already tried env var)
        if not self._client:
            logger.debug(
                f"Secret Manager client not available. Secret '{secret_name}' not found in environment."
            )
            return None

        # Try to get secret from Secret Manager
        try:
            # Build the resource name of the secret version.
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self._client.access_secret_version(request={"name": name})
            secret_payload = response.payload.data.decode("UTF-8")
            logger.debug(f"Retrieved secret '{secret_name}' from Secret Manager.")
            return secret_payload
        except exceptions.NotFound:
            logger.warning(
                f"Secret '{secret_name}' not found in Secret Manager or environment."
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error accessing secret '{secret_name}' from Secret Manager: {e}"
            )
            return None


# Create a singleton instance for convenience
secret_manager = SecretManager()


def get_secret(secret_name: str, version: str = "latest") -> Optional[str]:
    """
    Convenience function to get a secret using the singleton SecretManager instance.

    Args:
        secret_name: The name of the secret.
        version: The version of the secret (default: "latest").

    Returns:
        The secret value as a string, or None if not found.
    """
    return secret_manager.get_secret(secret_name, version)
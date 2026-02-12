"""Secret management abstraction layer."""
import os
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecretProvider(ABC):
    """Abstract interface for secret management."""

    @abstractmethod
    def get_secret(self, name: str) -> str:
        """Get secret value by name."""
        pass


class EnvSecretProvider(SecretProvider):
    """Secret provider that reads from environment variables."""

    def __init__(self):
        logger.info("EnvSecretProvider initialized")

    def get_secret(self, name: str) -> str:
        """Get secret from environment variable."""
        value = os.getenv(name)
        if value is None:
            raise ValueError(f"Secret '{name}' not found in environment variables")
        return value


class GcpSecretProvider(SecretProvider):
    """Secret provider that reads from GCP Secret Manager."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize GCP Secret Manager client.
        
        Args:
            project_id: GCP project ID. If None, uses default.
        """
        try:
            from google.cloud import secretmanager
            self.client = secretmanager.SecretManagerServiceClient()
            self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
            if not self.project_id:
                raise ValueError("GCP_PROJECT_ID must be set for GcpSecretProvider")
            logger.info(f"GcpSecretProvider initialized with project: {self.project_id}")
        except ImportError:
            raise ImportError("google-cloud-secret-manager is required for GcpSecretProvider")

    def get_secret(self, name: str) -> str:
        """Get secret from GCP Secret Manager."""
        # Normalize name: GOOGLE_API_KEY -> google-api-key
        secret_id = name.lower().replace("_", "-")
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to access secret '{name}' (as '{secret_id}'): {e}")
            raise ValueError(f"Secret '{name}' not found in Secret Manager") from e


def create_secret_provider(provider_type: Optional[str] = None) -> SecretProvider:
    """
    Factory function to create appropriate SecretProvider.
    
    Args:
        provider_type: Type of provider ('env' or 'gcp'). 
                      If None, reads from SECRET_PROVIDER_TYPE env var.
    
    Returns:
        SecretProvider instance
    """
    if provider_type is None:
        provider_type = os.getenv("SECRET_PROVIDER_TYPE", "env")
    
    provider_type = provider_type.lower()
    
    if provider_type == "env":
        return EnvSecretProvider()
    elif provider_type == "gcp":
        project_id = os.getenv("GCP_PROJECT_ID")
        return GcpSecretProvider(project_id=project_id)
    else:
        raise ValueError(f"Unknown secret provider type: {provider_type}")

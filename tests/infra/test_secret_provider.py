"""Tests for SecretProvider abstraction."""
import os
import pytest
from infra.secret_provider import (
    EnvSecretProvider,
    create_secret_provider,
)


class TestEnvSecretProvider:
    """Test EnvSecretProvider implementation."""

    def test_get_secret_success(self, monkeypatch):
        """Test getting secret from environment variable."""
        monkeypatch.setenv("TEST_SECRET", "secret_value")
        
        provider = EnvSecretProvider()
        result = provider.get_secret("TEST_SECRET")
        
        assert result == "secret_value"

    def test_get_secret_not_found(self, monkeypatch):
        """Test error when secret not found."""
        monkeypatch.delenv("NONEXISTENT_SECRET", raising=False)
        
        provider = EnvSecretProvider()
        
        with pytest.raises(ValueError, match="Secret 'NONEXISTENT_SECRET' not found"):
            provider.get_secret("NONEXISTENT_SECRET")


class TestSecretProviderFactory:
    """Test secret provider factory function."""

    def test_create_env_provider(self, monkeypatch):
        """Test creating EnvSecretProvider via factory."""
        monkeypatch.setenv("SECRET_PROVIDER_TYPE", "env")
        
        provider = create_secret_provider()
        assert isinstance(provider, EnvSecretProvider)

    def test_create_env_provider_default(self, monkeypatch):
        """Test default is EnvSecretProvider."""
        monkeypatch.delenv("SECRET_PROVIDER_TYPE", raising=False)
        
        provider = create_secret_provider()
        assert isinstance(provider, EnvSecretProvider)

    def test_invalid_provider_type(self):
        """Test invalid provider type raises error."""
        with pytest.raises(ValueError, match="Unknown secret provider type"):
            create_secret_provider("invalid_type")

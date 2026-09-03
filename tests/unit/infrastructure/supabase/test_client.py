"""Testes unitários do gerenciador e fábrica de clientes Supabase."""

from unittest.mock import MagicMock, patch
import pytest

from app.infrastructure.supabase.client import (
    SupabaseClientManager,
    get_supabase_admin_client,
    get_supabase_client,
)
from app.infrastructure.supabase.config import SupabaseConfig
from app.infrastructure.supabase.exceptions import (
    SupabaseConfigurationError,
    SupabaseConnectionError,
)


@pytest.fixture(autouse=True)
def reset_client_manager():
    """Reset singleton/cached instances in SupabaseClientManager before each test."""
    SupabaseClientManager.reset()
    yield
    SupabaseClientManager.reset()


def test_get_client_instantiation_success():
    """Verify that get_client initializes and returns a Supabase Client."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")
    mock_client_instance = MagicMock()

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client_instance,
    ) as mock_create:
        client = SupabaseClientManager.get_client(config)
        assert client == mock_client_instance
        mock_create.assert_called_once_with("https://test.supabase.co", "test-key")


def test_get_client_cached_instance():
    """Verify that subsequent calls return the cached client instance."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")
    mock_client_instance = MagicMock()

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client_instance,
    ) as mock_create:
        client1 = SupabaseClientManager.get_client(config)
        client2 = SupabaseClientManager.get_client(config)
        assert client1 is client2
        assert mock_create.call_count == 1


def test_get_admin_client_success():
    """Verify that get_admin_client uses service_role_key when provided."""
    config = SupabaseConfig(
        url="https://test.supabase.co",
        key="test-key",
        service_role_key="service-role-secret",
    )
    mock_admin_instance = MagicMock()

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_admin_instance,
    ) as mock_create:
        admin_client = SupabaseClientManager.get_admin_client(config)
        assert admin_client == mock_admin_instance
        mock_create.assert_called_once_with("https://test.supabase.co", "service-role-secret")


def test_get_admin_client_missing_service_key():
    """Verify that get_admin_client raises error when service_role_key is not configured."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key", service_role_key=None)
    with pytest.raises(SupabaseConfigurationError, match="service_role_key is not configured"):
        SupabaseClientManager.get_admin_client(config)


def test_get_client_connection_error():
    """Verify that client initialization failure raises SupabaseConnectionError."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")

    with patch(
        "app.infrastructure.supabase.client.create_client",
        side_effect=Exception("Network failure"),
    ):
        with pytest.raises(SupabaseConnectionError, match="Failed to initialize Supabase client"):
            SupabaseClientManager.get_client(config)


def test_health_check_success():
    """Verify health check returns healthy status when connection succeeds."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client,
    ):
        manager = SupabaseClientManager(config)
        result = manager.health_check()
        assert result["status"] == "healthy"
        assert result["url"] == "https://test.supabase.co"
        assert result["connected"] is True


def test_health_check_failure():
    """Verify health check returns unhealthy status without crashing on network error."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")
    mock_client = MagicMock()
    mock_client.auth.get_session.side_effect = Exception("Connection timed out")

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client,
    ):
        manager = SupabaseClientManager(config)
        result = manager.health_check()
        assert result["status"] == "unhealthy"
        assert result["connected"] is False
        assert "Connection timed out" in result["error"]


def test_get_supabase_client_convenience_function():
    """Verify convenience function get_supabase_client delegates to manager."""
    config = SupabaseConfig(url="https://test.supabase.co", key="test-key")
    mock_client = MagicMock()

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client,
    ):
        client = get_supabase_client(config)
        assert client == mock_client


def test_get_supabase_admin_client_convenience_function():
    """Verify convenience function get_supabase_admin_client delegates to manager."""
    config = SupabaseConfig(
        url="https://test.supabase.co",
        key="test-key",
        service_role_key="test-admin-key",
    )
    mock_client = MagicMock()

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client,
    ):
        client = get_supabase_admin_client(config)
        assert client == mock_client

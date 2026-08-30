"""Supabase client manager and connection lifecycle handlers."""

import logging
from typing import Any
from supabase import Client, create_client

from app.infrastructure.supabase.config import SupabaseConfig
from app.infrastructure.supabase.exceptions import (
    SupabaseConfigurationError,
    SupabaseConnectionError,
)

logger = logging.getLogger(__name__)


class SupabaseClientManager:
    """Manages the creation, caching, and health checking of Supabase clients."""

    _instance: Client | None = None
    _admin_instance: Client | None = None

    def __init__(self, config: SupabaseConfig | None = None) -> None:
        self.config = config or SupabaseConfig.from_env()

    @classmethod
    def get_client(cls, config: SupabaseConfig | None = None) -> Client:
        """Get or initialize the standard Supabase client.

        Args:
            config: Optional explicit SupabaseConfig. If omitted, loads from env.

        Returns:
            Client: Initialized Supabase client instance.

        Raises:
            SupabaseConnectionError: If client creation fails.
        """
        if cls._instance is not None:
            return cls._instance

        cfg = config or SupabaseConfig.from_env()
        cfg.validate()

        try:
            cls._instance = create_client(cfg.url, cfg.key)
            logger.info("Supabase client initialized successfully for %s", cfg.url)
            return cls._instance
        except Exception as exc:
            logger.error("Failed to initialize Supabase client for %s: %s", cfg.url, exc)
            raise SupabaseConnectionError(f"Failed to initialize Supabase client: {exc}") from exc

    @classmethod
    def get_admin_client(cls, config: SupabaseConfig | None = None) -> Client:
        """Get or initialize the administrative Supabase client using service role key.

        Args:
            config: Optional explicit SupabaseConfig.

        Returns:
            Client: Initialized Supabase client with admin privileges.

        Raises:
            SupabaseConfigurationError: If service_role_key is not configured.
            SupabaseConnectionError: If client creation fails.
        """
        if cls._admin_instance is not None:
            return cls._admin_instance

        cfg = config or SupabaseConfig.from_env()
        cfg.validate()

        if not cfg.service_role_key:
            raise SupabaseConfigurationError(
                "Cannot create admin client: service_role_key is not configured in environment or config."
            )

        try:
            cls._admin_instance = create_client(cfg.url, cfg.service_role_key)
            logger.info("Supabase admin client initialized successfully for %s", cfg.url)
            return cls._admin_instance
        except Exception as exc:
            logger.error("Failed to initialize Supabase admin client for %s: %s", cfg.url, exc)
            raise SupabaseConnectionError(
                f"Failed to initialize Supabase admin client: {exc}"
            ) from exc

    def health_check(self) -> dict[str, Any]:
        """Perform a connection health check.

        Returns:
            dict[str, Any]: Status summary containing 'status', 'url', and 'connected'.
        """
        try:
            client = self.get_client(self.config)
            # Lightweight auth check to verify API connectivity
            client.auth.get_session()
            return {
                "status": "healthy",
                "url": self.config.url,
                "connected": True,
            }
        except Exception as exc:
            logger.warning("Supabase health check failed for %s: %s", self.config.url, exc)
            return {
                "status": "unhealthy",
                "url": self.config.url,
                "connected": False,
                "error": str(exc),
            }

    @classmethod
    def reset(cls) -> None:
        """Reset cached client instances (primarily for testing)."""
        cls._instance = None
        cls._admin_instance = None


def get_supabase_client(config: SupabaseConfig | None = None) -> Client:
    """Convenience helper to obtain the default Supabase client.

    Args:
        config: Optional configuration. If None, loaded from environment.

    Returns:
        Client: Supabase client instance.
    """
    return SupabaseClientManager.get_client(config)


def get_supabase_admin_client(config: SupabaseConfig | None = None) -> Client:
    """Convenience helper to obtain the administrative Supabase client.

    Args:
        config: Optional configuration. If None, loaded from environment.

    Returns:
        Client: Supabase admin client instance with service role credentials.
    """
    return SupabaseClientManager.get_admin_client(config)

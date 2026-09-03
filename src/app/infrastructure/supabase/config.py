"""Configuration and environment management for Supabase."""

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from app.infrastructure.supabase.exceptions import SupabaseConfigurationError


def _mask_secret(secret: str | None) -> str:
    """Mask sensitive string for safe logging and representation."""
    if not secret:
        return "None"
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"


@dataclass(frozen=True)
class SupabaseConfig:
    """Configuration options required to connect to Supabase."""

    url: str
    key: str
    service_role_key: str | None = None
    schema: str = "public"
    timeout: float = 30.0

    def __repr__(self) -> str:
        """Safe representation that masks secret keys to prevent leakage in logs/traces."""
        return (
            f"SupabaseConfig("
            f"url='{self.url}', "
            f"key='{_mask_secret(self.key)}', "
            f"service_role_key='{_mask_secret(self.service_role_key)}', "
            f"schema='{self.schema}', "
            f"timeout={self.timeout})"
        )

    def __str__(self) -> str:
        """Safe string conversion that masks secret keys."""
        return self.__repr__()

    def validate(self) -> None:
        """Validate that all required configuration fields are present and valid.

        Raises:
            SupabaseConfigurationError: If any configuration value is invalid.
        """
        if not self.url or not self.url.strip():
            raise SupabaseConfigurationError("Supabase URL must not be empty.")

        parsed_url = urlparse(self.url)
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise SupabaseConfigurationError(
                f"Invalid Supabase URL scheme or format: '{self.url}'. Must start with http:// or https://"
            )

        if not self.key or not self.key.strip():
            raise SupabaseConfigurationError("Supabase API key must not be empty.")

    @classmethod
    def from_env(
        cls,
        env_file: str | Path | None = None,
        load_env: bool = True,
    ) -> "SupabaseConfig":
        """Load Supabase configuration from environment variables or .env file.

        Args:
            env_file: Optional path to a specific .env file.
            load_env: Whether to load variables from .env via dotenv (default: True).

        Supported environment variable aliases:
            - URL: SUPABASE_URL, SUPABASE_PROJECT_URL, NEXT_PUBLIC_SUPABASE_URL
            - Public Key: SUPABASE_KEY, SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_API_KEY, SUPABASE_PUBLIC_KEY, sb_publishable_key, SB_PUBLISHABLE_KEY
            - Service Key: SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SERVICE_KEY, SUPABASE_SECRET_KEY, sb_secret_key, SB_SECRET_KEY
            - Schema: SUPABASE_SCHEMA (default: 'public')
            - Timeout: SUPABASE_TIMEOUT (default: 30.0)

        Returns:
            SupabaseConfig: Populated and validated configuration instance.

        Raises:
            SupabaseConfigurationError: If required environment variables are missing.
        """
        if load_env and load_dotenv is not None:
            load_dotenv(dotenv_path=env_file, override=False)

        raw_url = (
            os.environ.get("SUPABASE_URL")
            or os.environ.get("SUPABASE_PROJECT_URL")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
            or ""
        ).strip()

        # Normalize URL by removing trailing slashes and /rest/v1 if inadvertently present
        url = raw_url.rstrip("/")
        if url.endswith("/rest/v1"):
            url = url[:-8].rstrip("/")

        key = (
            os.environ.get("SUPABASE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
            or os.environ.get("SUPABASE_API_KEY")
            or os.environ.get("SUPABASE_PUBLIC_KEY")
            or os.environ.get("sb_publishable_key")
            or os.environ.get("SB_PUBLISHABLE_KEY")
            or ""
        ).strip()

        service_role_key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_SERVICE_KEY")
            or os.environ.get("SUPABASE_SECRET_KEY")
            or os.environ.get("sb_secret_key")
            or os.environ.get("SB_SECRET_KEY")
            or ""
        ).strip() or None

        # If key wasn't provided but service_role_key was, allow fallback
        if not key and service_role_key:
            key = service_role_key

        schema = os.environ.get("SUPABASE_SCHEMA", "public").strip()
        timeout_str = os.environ.get("SUPABASE_TIMEOUT", "30.0").strip()

        if not url or not key:
            raise SupabaseConfigurationError(
                "Missing required Supabase environment variables: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY/sb_publishable_key)."
            )

        try:
            timeout = float(timeout_str)
        except ValueError:
            timeout = 30.0

        config = cls(
            url=url,
            key=key,
            service_role_key=service_role_key,
            schema=schema,
            timeout=timeout,
        )
        config.validate()
        return config

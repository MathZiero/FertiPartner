"""Testes unitários de configurações, variáveis de ambiente e exceções do Supabase."""

import os
from unittest.mock import patch
import pytest

from app.infrastructure.supabase.config import SupabaseConfig, _mask_secret
from app.infrastructure.supabase.exceptions import (
    SupabaseConfigurationError,
    SupabaseConnectionError,
    SupabaseIntegrationError,
    SupabaseQueryError,
    SupabaseRecordNotFoundError,
)


def test_exceptions_hierarchy():
    """Verify exception inheritance and basic error messages."""
    base_err = SupabaseIntegrationError("Base error")
    assert isinstance(base_err, Exception)

    cfg_err = SupabaseConfigurationError("Config missing")
    assert isinstance(cfg_err, SupabaseIntegrationError)

    conn_err = SupabaseConnectionError("Connection failed")
    assert isinstance(conn_err, SupabaseIntegrationError)

    query_err = SupabaseQueryError("Query failed")
    assert isinstance(query_err, SupabaseIntegrationError)

    not_found_err = SupabaseRecordNotFoundError("Record not found")
    assert isinstance(not_found_err, SupabaseIntegrationError)


def test_config_initialization_valid():
    """Verify SupabaseConfig creation with valid explicit parameters."""
    config = SupabaseConfig(
        url="https://xyzcompany.supabase.co",
        key="anon-key-token-secret-12345",
        service_role_key="service-role-token-secret-67890",
        schema="public",
        timeout=15.0,
    )
    assert config.url == "https://xyzcompany.supabase.co"
    assert config.key == "anon-key-token-secret-12345"
    assert config.service_role_key == "service-role-token-secret-67890"
    assert config.schema == "public"
    assert config.timeout == 15.0


def test_config_repr_and_str_masks_secrets():
    """Verify that repr() and str() of SupabaseConfig NEVER display raw secret keys in logs."""
    raw_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.super_secret_anon_token_12345"
    raw_service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.super_secret_service_role_67890"

    config = SupabaseConfig(
        url="https://xyzcompany.supabase.co",
        key=raw_key,
        service_role_key=raw_service_key,
    )

    repr_str = repr(config)
    str_str = str(config)

    # Must NOT contain the full secrets
    assert raw_key not in repr_str
    assert raw_service_key not in repr_str
    assert raw_key not in str_str
    assert raw_service_key not in str_str

    # Must contain masking markers
    assert "..." in repr_str
    assert "..." in str_str


def test_mask_secret_helper():
    """Verify _mask_secret handles None, short keys, and long keys safely."""
    assert _mask_secret(None) == "None"
    assert _mask_secret("") == "None"
    assert _mask_secret("short") == "***"
    assert _mask_secret("12345678") == "***"
    assert _mask_secret("1234567890") == "1234...7890"


def test_config_validation_missing_url():
    """Verify SupabaseConfig raises SupabaseConfigurationError when URL is missing or empty."""
    with pytest.raises(SupabaseConfigurationError, match="Supabase URL must not be empty"):
        SupabaseConfig(url="", key="anon-key-token").validate()


def test_config_validation_invalid_url():
    """Verify SupabaseConfig raises SupabaseConfigurationError when URL is malformed."""
    with pytest.raises(SupabaseConfigurationError, match="Invalid Supabase URL scheme"):
        SupabaseConfig(url="not-a-valid-url", key="anon-key-token").validate()


def test_config_validation_missing_key():
    """Verify SupabaseConfig raises SupabaseConfigurationError when API key is missing."""
    with pytest.raises(SupabaseConfigurationError, match="Supabase API key must not be empty"):
        SupabaseConfig(url="https://xyz.supabase.co", key="").validate()


def test_config_from_env_success():
    """Verify SupabaseConfig.from_env() correctly loads from environment variables."""
    mock_env = {
        "SUPABASE_URL": "https://sample-project.supabase.co",
        "SUPABASE_KEY": "sample-key-123",
        "SUPABASE_SERVICE_ROLE_KEY": "admin-secret-456",
        "SUPABASE_SCHEMA": "analytics",
        "SUPABASE_TIMEOUT": "20.5",
    }
    with patch.dict(os.environ, mock_env, clear=False):
        config = SupabaseConfig.from_env(load_env=False)
        assert config.url == "https://sample-project.supabase.co"
        assert config.key == "sample-key-123"
        assert config.service_role_key == "admin-secret-456"
        assert config.schema == "analytics"
        assert config.timeout == 20.5


def test_config_from_env_fallback_alternative_names():
    """Verify SupabaseConfig.from_env() supports standard alias env variable names."""
    mock_env = {
        "SUPABASE_PROJECT_URL": "https://sample-project.supabase.co",
        "SUPABASE_ANON_KEY": "sample-anon-key",
        "SUPABASE_SERVICE_KEY": "sample-service-key",
    }
    with patch.dict(os.environ, mock_env, clear=True):
        config = SupabaseConfig.from_env(load_env=False)
        assert config.url == "https://sample-project.supabase.co"
        assert config.key == "sample-anon-key"
        assert config.service_role_key == "sample-service-key"


def test_config_from_env_missing_vars():
    """Verify SupabaseConfig.from_env() raises error if required variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SupabaseConfigurationError, match="Missing required Supabase environment variables"):
            # Disable dotenv loading during this isolated test
            SupabaseConfig.from_env(load_env=False)


def test_config_from_env_new_supabase_key_format_and_url_cleaning():
    """Verify SupabaseConfig.from_env() supports sb_publishable_key, sb_secret_key, and cleans /rest/v1."""
    mock_env = {
        "SUPABASE_URL": "https://ghfbgcrvetskgntazdut.supabase.co/rest/v1/",
        "sb_publishable_key": "sb_publishable_bOue9oc4Y1NhszCVJZtaDw_FECPdEKI",
        "sb_secret_key": "sb_secret_-RKKEckrWhKE2AYLOxKong_35f1AiVJ",
    }
    with patch.dict(os.environ, mock_env, clear=True):
        config = SupabaseConfig.from_env(load_env=False)
        assert config.url == "https://ghfbgcrvetskgntazdut.supabase.co"
        assert config.key == "sb_publishable_bOue9oc4Y1NhszCVJZtaDw_FECPdEKI"
        assert config.service_role_key == "sb_secret_-RKKEckrWhKE2AYLOxKong_35f1AiVJ"

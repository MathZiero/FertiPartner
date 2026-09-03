"""Testes unitários do gerenciador de autenticação e validação de tokens do FAOSTAT."""

import base64
import json
import time
import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.faostat.auth import (
    FAOSTATAuthManager,
    decode_jwt_payload,
    is_token_valid,
)


def create_fake_jwt(username: str, exp_offset_seconds: int) -> str:
    """Helper to create dummy JWT for testing expiration logic."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload_data = {
        "username": username,
        "iat": int(time.time()),
        "exp": int(time.time() + exp_offset_seconds),
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    return f"{header}.{payload}.signature"


def test_decode_jwt_payload_success():
    token = create_fake_jwt("test_user", 3600)
    payload = decode_jwt_payload(token)
    assert payload is not None
    assert payload.get("username") == "test_user"
    assert "exp" in payload


def test_decode_jwt_payload_invalid_token():
    assert decode_jwt_payload("invalid-token") is None
    assert decode_jwt_payload("") is None


def test_is_token_valid_when_fresh():
    fresh_token = create_fake_jwt("active_user", 3600)
    assert is_token_valid(fresh_token) is True


def test_is_token_valid_when_expired():
    expired_token = create_fake_jwt("old_user", -60)
    assert is_token_valid(expired_token) is False


def test_is_token_valid_when_close_to_expiry():
    # Buffer is 120 seconds by default, so a token expiring in 60 seconds should be treated as invalid
    close_token = create_fake_jwt("soon_user", 60)
    assert is_token_valid(close_token, buffer_seconds=120) is False


def test_auth_manager_returns_cached_valid_token():
    valid_token = create_fake_jwt("cached_user", 1800)
    manager = FAOSTATAuthManager(token=valid_token)
    assert manager.get_token() == valid_token


def test_auth_manager_raises_when_expired_and_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("FAOSTAT_USERNAME", raising=False)
    monkeypatch.delenv("FAOSTAT_PASSWORD", raising=False)
    empty_env = tmp_path / "empty.env"
    empty_env.write_text("", encoding="utf-8")

    expired_token = create_fake_jwt("old_user", -10)
    manager = FAOSTATAuthManager(token=expired_token, username=None, password=None, env_file=empty_env)
    with pytest.raises(ValueError, match="FAOSTAT_USERNAME / FAOSTAT_PASSWORD are not configured"):
        manager.get_token()


@patch("httpx.Client.post")
def test_auth_manager_login_success(mock_post, tmp_path):
    fake_env = tmp_path / ".env"
    fake_env.write_text("FAOSTAT_TOKEN=old\n", encoding="utf-8")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "AuthenticationResult": {
            "AccessToken": "fresh_access_token_123",
            "RefreshToken": "fresh_refresh_token_456",
            "ExpiresIn": 3600,
        }
    }
    mock_post.return_value = mock_response

    manager = FAOSTATAuthManager(
        username="user@example.com",
        password="secure_password",
        env_file=fake_env,
    )

    new_token = manager.login(persist_to_env=True)
    assert new_token == "fresh_access_token_123"
    assert manager.current_token == "fresh_access_token_123"

    # Verify .env was updated
    content = fake_env.read_text(encoding="utf-8")
    assert "fresh_access_token_123" in content

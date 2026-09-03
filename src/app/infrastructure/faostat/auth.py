"""Gerenciamento de autenticação, renovação e validação de tokens JWT do FAOSTAT."""

import base64
import json
import logging
import os
from pathlib import Path
import time
from typing import Any
import httpx
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

FAOSTAT_LOGIN_URL = "https://faostatservices.fao.org/api/v1/auth/login"
DEFAULT_EXPIRATION_BUFFER_SECONDS = 120  # Refresh if within 2 minutes of expiry


def decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode unverified JWT payload to inspect standard claims like 'exp'."""
    try:
        parts = token.strip().split(".")
        if len(parts) < 2:
            return None
        # Add necessary base64 padding
        payload_b64 = parts[1] + "==="
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        logger.debug("Failed to decode JWT payload: %s", exc)
        return None


def is_token_valid(token: str | None, buffer_seconds: int = DEFAULT_EXPIRATION_BUFFER_SECONDS) -> bool:
    """Check whether a JWT token is present and not expired."""
    if not token or not token.strip():
        return False

    payload = decode_jwt_payload(token)
    if not payload or "exp" not in payload:
        return False

    exp_timestamp = float(payload["exp"])
    current_time = time.time()
    return current_time + buffer_seconds < exp_timestamp


class FAOSTATAuthManager:
    """Manages FAOSTAT token generation, caching, and automatic renewal."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        env_file: Path | str | None = None,
    ) -> None:
        self.env_file = Path(env_file) if env_file else Path(".env")
        if self.env_file.exists():
            load_dotenv(self.env_file, override=False)

        self.username = username or os.environ.get("FAOSTAT_USERNAME")
        self.password = password or os.environ.get("FAOSTAT_PASSWORD")
        self._current_token = token or os.environ.get("FAOSTAT_TOKEN")
        self._refresh_token = os.environ.get("FAOSTAT_REFRESH_TOKEN")

    @property
    def current_token(self) -> str | None:
        """Return the current token in memory."""
        return self._current_token

    def get_token(self, force_refresh: bool = False, persist_to_env: bool = True) -> str:
        """Get an active, valid FAOSTAT token.

        If the current token is still valid, returns it immediately.
        Otherwise, performs programmatic login to retrieve a fresh token.

        Args:
            force_refresh: Force new login even if token appears valid.
            persist_to_env: Save the new token into the .env file.

        Returns:
            str: Valid Bearer access token.

        Raises:
            ValueError: If credentials are missing or login fails.
        """
        if not force_refresh and is_token_valid(self._current_token):
            return self._current_token  # type: ignore[return-value]

        if not self.username or not self.password:
            raise ValueError(
                "FAOSTAT token is missing or expired, and FAOSTAT_USERNAME / FAOSTAT_PASSWORD "
                "are not configured. Please provide credentials to obtain a new token."
            )

        logger.info("Obtaining fresh FAOSTAT token via programmatic login (%s)...", self.username)
        new_token = self.login(persist_to_env=persist_to_env)
        return new_token

    def login(self, persist_to_env: bool = True) -> str:
        """Execute POST /auth/login and extract AccessToken."""
        payload = {
            "username": self.username,
            "password": self.password,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(FAOSTAT_LOGIN_URL, data=payload, headers=headers)

            if response.status_code != 200:
                raise ValueError(
                    f"FAOSTAT login failed ({response.status_code}): {response.text}"
                )

            data = response.json()
            auth_result = data.get("AuthenticationResult", {})
            access_token = auth_result.get("AccessToken")
            refresh_token = auth_result.get("RefreshToken")

            if not access_token:
                raise ValueError(f"No AccessToken returned in auth response: {data}")

            self._current_token = access_token
            if refresh_token:
                self._refresh_token = refresh_token

            logger.info("FAOSTAT authentication successful! Token acquired.")

            if persist_to_env and self.env_file.exists():
                try:
                    set_key(str(self.env_file), "FAOSTAT_TOKEN", access_token)
                    if refresh_token:
                        set_key(str(self.env_file), "FAOSTAT_REFRESH_TOKEN", refresh_token)
                    logger.info("Updated FAOSTAT_TOKEN in %s", self.env_file)
                except Exception as exc:
                    logger.warning("Could not persist new token to .env: %s", exc)

            return access_token

        except httpx.HTTPError as exc:
            logger.error("HTTP error connecting to FAOSTAT login: %s", exc)
            raise


def get_valid_faostat_token() -> str:
    """Convenience helper to retrieve an active FAOSTAT token."""
    manager = FAOSTATAuthManager()
    return manager.get_token()

"""Cliente HTTP resiliente com controle de taxa (rate limit), retentativas exponenciais e jitter."""

import logging
import random
import time
from typing import Any, Mapping
import httpx

logger = logging.getLogger(__name__)


class ResilientHttpClient:
    """HTTP Client with integrated rate limiting and retry logic."""

    def __init__(
        self,
        min_interval_seconds: float = 1.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 2.0,
        max_backoff_seconds: float = 30.0,
        timeout_seconds: float = 20.0,
        verify_ssl: bool = True,
        default_headers: Mapping[str, str] | None = None,
    ) -> None:
        self.min_interval_seconds = min_interval_seconds
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl
        self.default_headers = dict(default_headers or {})
        self._last_request_timestamp: float = 0.0

    def _enforce_rate_limit(self) -> None:
        """Enforce spacing between consecutive requests to prevent bursting."""
        elapsed = time.time() - self._last_request_timestamp
        if elapsed < self.min_interval_seconds:
            sleep_duration = self.min_interval_seconds - elapsed
            logger.debug("Rate limiting: sleeping %.2f seconds", sleep_duration)
            time.sleep(sleep_duration)
        self._last_request_timestamp = time.time()

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with full jitter."""
        exponential = self.base_backoff_seconds * (2 ** attempt)
        ceiling = min(self.max_backoff_seconds, exponential)
        return random.uniform(0.5, ceiling)

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> httpx.Response:
        """Execute an HTTP request with rate limiting and exponential retries."""
        combined_headers = {**self.default_headers, **(headers or {})}
        attempt = 0

        while True:
            self._enforce_rate_limit()
            attempt += 1

            try:
                with httpx.Client(timeout=self.timeout_seconds, verify=self.verify_ssl) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        headers=combined_headers,
                        params=params,
                        json=json,
                        data=data,
                    )

                # Check for Comex Stat specific throttling text
                is_comex_throttle = (
                    response.status_code == 200
                    and "excedeu o limite de solicitações" in response.text
                )

                if response.status_code == 429 or is_comex_throttle:
                    cool_off = 12.0 if is_comex_throttle else self._calculate_backoff(attempt)
                    logger.warning(
                        "Rate limit exceeded on %s (attempt %d/%d). Sleeping %.1fs...",
                        url, attempt, self.max_retries, cool_off
                    )
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    time.sleep(cool_off)
                    continue

                if response.status_code in (500, 502, 503, 504):
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Server error %d on %s (attempt %d/%d). Retrying in %.1fs...",
                        response.status_code, url, attempt, self.max_retries, backoff
                    )
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    time.sleep(backoff)
                    continue

                response.raise_for_status()
                return response

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                backoff = self._calculate_backoff(attempt)
                logger.warning(
                    "Network error on %s: %s (attempt %d/%d). Retrying in %.1fs...",
                    url, exc, attempt, self.max_retries, backoff
                )
                if attempt > self.max_retries:
                    raise
                time.sleep(backoff)

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Convenience GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Convenience POST request."""
        return self.request("POST", url, **kwargs)

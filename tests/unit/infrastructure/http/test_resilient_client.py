"""Testes unitários do cliente HTTP resiliente (rate limiting, retentativas e espaçamento)."""

import time
import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.http import ResilientHttpClient
import httpx


def test_rate_limiting_spacing():
    client = ResilientHttpClient(min_interval_seconds=0.1)
    t0 = time.time()
    with patch("httpx.Client.request") as mock_request:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"ok": true}'
        mock_request.return_value = mock_resp

        client.get("https://example.com/api/1")
        client.get("https://example.com/api/2")

    elapsed = time.time() - t0
    assert elapsed >= 0.1, f"Expected at least 0.1s spacing, got {elapsed}s"


@patch("httpx.Client.request")
def test_retry_on_server_error_and_succeed(mock_request):
    client = ResilientHttpClient(min_interval_seconds=0.01, base_backoff_seconds=0.05, max_retries=2)

    error_resp = MagicMock()
    error_resp.status_code = 503
    error_resp.text = "Service Unavailable"
    error_resp.raise_for_status.side_effect = httpx.HTTPStatusError("503", request=MagicMock(), response=error_resp)

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.text = '{"data": "success"}'

    mock_request.side_effect = [error_resp, ok_resp]

    res = client.get("https://example.com/retry")
    assert res.status_code == 200
    assert mock_request.call_count == 2


@patch("httpx.Client.request")
def test_comex_throttle_cooloff_handling(mock_request):
    client = ResilientHttpClient(min_interval_seconds=0.01, base_backoff_seconds=0.05, max_retries=2)

    throttled_resp = MagicMock()
    throttled_resp.status_code = 200
    throttled_resp.text = "Você excedeu o limite de solicitações. Por favor, tente novamente em 10 segundos."

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.text = '{"data": {"list": [1, 2, 3]}}'

    mock_request.side_effect = [throttled_resp, ok_resp]

    with patch("time.sleep") as mock_sleep:
        res = client.post("https://api-comexstat.mdic.gov.br/general")
        assert res.status_code == 200
        # Check that 12s sleep was triggered
        mock_sleep.assert_any_call(12.0)

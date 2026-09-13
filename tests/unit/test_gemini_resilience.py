"""Testes unitários de TDD para resiliência de quotas multi-modelos e resolução segura de chaves do Gemini."""

import os
from unittest.mock import MagicMock, patch
import pytest

from app.domain.ai.entities import ChatMessage, ChatRole
from app.infrastructure.ai.gemini_client import GeminiClient, mask_secret
from app.presentation.streamlit.services.ai_service import FertiAIService


def test_mask_secret_protects_credentials():
    """Valida que tokens são mascarados adequadamente sem expor a credencial real."""
    assert mask_secret("") == "None"
    assert mask_secret(None) == "None"
    assert mask_secret("short") == "***"
    masked = mask_secret("AIzaSy1234567890abcdefXYZ")
    assert masked.startswith("AIza...")
    assert "1234567890abcdef" not in masked


def test_gemini_client_reads_gemini_api_env_alias():
    """Garante que a resolução de chaves aceita o alias GEMINI_API definido no .env."""
    with patch.dict(os.environ, {"GEMINI_API": "AIzaSyTestAliasKeyFromEnv12345"}, clear=True):
        client = GeminiClient()
        assert client.api_key == "AIzaSyTestAliasKeyFromEnv12345"
        assert client.is_configured()


def test_gemini_client_fallback_on_429_quota_exceeded():
    """Valida failover automático para outro modelo do pool quando o primeiro atinge cota 429."""
    client = GeminiClient(
        api_key="AIzaSyFakeKeyTest12345",
        model_name="gemini-3.6-flash",
        fallback_models=["gemini-3.6-flash", "gemini-3.8-flash"],
    )

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.text = '{"error": {"code": 429, "message": "Resource has been exhausted (quota)."}}'

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "candidates": [
            {
                "content": {"parts": [{"text": "Resposta obtida pelo modelo secundário!"}]},
                "finishReason": "STOP",
            }
        ]
    }

    # Primeiro modelo recebe 429; failover tenta o segundo modelo que responde 200 OK
    with patch("httpx.Client.post", side_effect=[resp_429, resp_200]):
        res = client.generate_content([ChatMessage(role=ChatRole.USER, content="Análise NPK")])
        assert res.is_success
        assert "modelo secundário" in res.content
        assert res.model_used == "gemini-3.8-flash"


def test_gemini_client_all_models_429_returns_clear_quota_error():
    """Garante mensagem amigável e explicativa quando todos os modelos do pool esgotam a cota."""
    client = GeminiClient(
        api_key="AIzaSyFakeKeyTest12345",
        model_name="gemini-3.6-flash",
        fallback_models=["gemini-3.6-flash", "gemini-3.8-flash"],
    )

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.text = '{"error": {"code": 429, "message": "Quota exceeded"}}'

    with patch("httpx.Client.post", return_value=resp_429):
        res = client.generate_content([ChatMessage(role=ChatRole.USER, content="Análise NPK")])
        assert not res.is_success
        assert res.error_message is not None
        assert "cota" in res.error_message.lower() or "limite" in res.error_message.lower()


def test_ferti_ai_service_precedence_user_vs_system_default():
    """Valida precedência de chaves: chave do usuário na sessão sobrepõe a padrão do .env."""
    with patch.dict(os.environ, {"GEMINI_API": "AIzaSySystemDefaultKey"}, clear=True):
        # 1. Sem chave de usuário na sessão: usa a padrão do sistema (.env)
        with patch("streamlit.session_state", {}):
            key = FertiAIService.get_api_key()
            assert key == "AIzaSySystemDefaultKey"
            assert FertiAIService.is_using_user_key() is False

        # 2. Com chave de usuário informada na sessão: ela tem precedência
        with patch("streamlit.session_state", {"user_gemini_api_key": "AIzaSyCustomUserKey"}):
            key = FertiAIService.get_api_key()
            assert key == "AIzaSyCustomUserKey"
            assert FertiAIService.is_using_user_key() is True

"""Cliente de integração com a API do Google Gemini (generateContent)."""

import json
import logging
from typing import Any
import httpx

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class GeminiClient:
    """Cliente HTTP resiliente para a API Google Gemini v1beta."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or ""
        self.model_name = model_name or self.DEFAULT_MODEL
        self._http_client = httpx.Client(timeout=35.0)

    def is_configured(self) -> bool:
        """Verifica se a chave da API está devidamente configurada."""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def _convert_messages_to_gemini_contents(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Converte mensagens do domínio FertiPartner para o formato da API Gemini."""
        contents: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == ChatRole.USER:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == ChatRole.MODEL:
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                for tc in msg.tool_calls:
                    parts.append({
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.args,
                        }
                    })
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif msg.role == ChatRole.TOOL:
                parts = []
                for tr in msg.tool_results:
                    parts.append({
                        "functionResponse": {
                            "name": tr.name,
                            "response": {"output": tr.content},
                        }
                    })
                if parts:
                    contents.append({"role": "user", "parts": parts})

        return contents

    def generate_content(
        self,
        messages: list[ChatMessage],
        system_instruction: str | None = None,
        tools_declarations: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> AIResponse:
        """Envia requisição para a API do Google Gemini com suporte a Function Calling."""
        if not self.is_configured():
            return AIResponse(
                content="",
                is_success=False,
                error_message="Chave de API do Google Gemini não configurada. Insira sua chave para utilizar os recursos de IA.",
            )

        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"

        contents = self._convert_messages_to_gemini_contents(messages)
        if not contents:
            return AIResponse(content="", is_success=False, error_message="Nenhuma mensagem para envio.")

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if tools_declarations:
            payload["tools"] = [
                {"functionDeclarations": tools_declarations}
            ]

        try:
            resp = self._http_client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return AIResponse(
                        content="Não foi possível gerar uma resposta para esta consulta.",
                        is_success=True,
                    )

                first_candidate = candidates[0]
                content_obj = first_candidate.get("content", {})
                parts = content_obj.get("parts", [])

                text_fragments: list[str] = []
                tool_calls: list[ToolCall] = []

                for part in parts:
                    if "text" in part and part["text"]:
                        text_fragments.append(part["text"])
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        tool_calls.append(ToolCall(name=fc.get("name", ""), args=fc.get("args", {})))

                finish_reason = first_candidate.get("finishReason", "STOP")
                full_text = "".join(text_fragments).strip()

                return AIResponse(
                    content=full_text,
                    tool_calls=tool_calls,
                    is_success=True,
                    finish_reason=finish_reason,
                )

            elif resp.status_code in (400, 401, 403):
                err_data = resp.json().get("error", {})
                err_msg = err_data.get("message", "Chave de API inválida ou sem permissão de acesso.")
                logger.warning("Falha de autenticação no Gemini: %s", err_msg)
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message=f"Erro de autenticação no Google Gemini: {err_msg}",
                )
            elif resp.status_code == 429:
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message="Limite de taxa (rate limit / cota gratuita) atingido na API do Gemini. Aguarde alguns segundos.",
                )
            else:
                logger.error("Erro na API Gemini: HTTP %s - %s", resp.status_code, resp.text)
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message=f"Falha na comunicação com o Google Gemini (HTTP {resp.status_code}).",
                )

        except httpx.TimeoutException:
            logger.error("Timeout na requisição para a API do Gemini.")
            return AIResponse(
                content="",
                is_success=False,
                error_message="Tempo limite de resposta esgotado na comunicação com a API do Google Gemini.",
            )
        except Exception as exc:
            logger.exception("Exceção inesperada ao consultar a API do Gemini: %s", exc)
            return AIResponse(
                content="",
                is_success=False,
                error_message=f"Erro ao conectar com a API do Gemini: {str(exc)}",
            )

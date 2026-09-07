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
    DEFAULT_MODEL = "gemini-3.6-flash"

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key or ""
        self.model_name = (model_name or self.DEFAULT_MODEL).removeprefix("models/")
        self._http_client = httpx.Client(
            timeout=httpx.Timeout(90.0, connect=20.0, read=90.0, write=30.0)
        )

    @classmethod
    def list_available_models(cls, api_key: str) -> list[str]:
        """Consulta a API do Google AI Studio para listar modelos disponíveis suportando generateContent.

        Filtra modelos depreciados e prioriza os modelos recomendados da série 3.x.
        Retorna fallback seguro caso a API não responda ou a chave esteja ausente.
        """
        fallback = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.1-pro"]
        if not api_key or len(api_key.strip()) < 10:
            return fallback

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    models = data.get("models", [])
                    valid_models: list[str] = []
                    deprecated_tokens = ["1.0", "1.5", "2.0", "2.5", "vision", "text-bison", "chat-bison"]
                    for m in models:
                        name = m.get("name", "").removeprefix("models/")
                        supported = m.get("supportedGenerationMethods", [])
                        if "generateContent" in supported and name.startswith("gemini-"):
                            if not any(dep in name for dep in deprecated_tokens):
                                valid_models.append(name)

                    if valid_models:
                        if "gemini-3.6-flash" in valid_models:
                            valid_models.remove("gemini-3.6-flash")
                            valid_models.insert(0, "gemini-3.6-flash")
                        return valid_models
        except Exception as exc:
            logger.warning("Falha na descoberta de modelos Gemini via API: %s", exc)

        return fallback

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
                    call_obj: dict[str, Any] = {
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.args,
                        }
                    }
                    if tc.id:
                        call_obj["functionCall"]["id"] = tc.id
                    parts.append(call_obj)
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif msg.role == ChatRole.TOOL:
                parts = []
                for tr in msg.tool_results:
                    resp_obj: dict[str, Any] = {
                        "functionResponse": {
                            "name": tr.name,
                            "response": {"output": tr.content},
                        }
                    }
                    if tr.id:
                        resp_obj["functionResponse"]["id"] = tr.id
                    parts.append(resp_obj)
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

        gen_config: dict[str, Any] = {
            "maxOutputTokens": 2048,
        }
        # Na série Gemini 3.x, ativa thinkingLevel LOW para respostas ágeis sem timeout em chat
        if self.model_name.startswith("gemini-3"):
            gen_config["thinkingConfig"] = {
                "thinkingLevel": "LOW",
            }
        elif temperature is not None:
            gen_config["temperature"] = temperature

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
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
                    if part.get("thought", False):
                        continue
                    if "text" in part and part["text"]:
                        text_fragments.append(part["text"])
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        tool_calls.append(
                            ToolCall(
                                name=fc.get("name", ""),
                                args=fc.get("args", {}),
                                id=fc.get("id"),
                            )
                        )

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
                err_msg = err_data.get("message", "Chave de API inválida ou parâmetros incorretos.")
                logger.warning("Falha de autenticação/parâmetros no Gemini: %s", err_msg)
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message=f"Erro no Google Gemini: {err_msg}",
                )
            elif resp.status_code == 404:
                err_data = resp.json().get("error", {})
                err_msg = err_data.get("message", f"O modelo '{self.model_name}' não está disponível ou foi depreciado.")
                logger.warning("Modelo Gemini indisponível (HTTP 404): %s", err_msg)
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message=f"Modelo Gemini indisponível: {err_msg}",
                )
            elif resp.status_code == 429:
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message="Limite de taxa (rate limit / cota gratuita) atingido na API do Gemini. Aguarde alguns segundos.",
                )
            else:
                err_msg = ""
                try:
                    err_msg = resp.json().get("error", {}).get("message", "")
                except Exception:
                    pass
                detail = f": {err_msg}" if err_msg else f" (HTTP {resp.status_code})."
                logger.error("Erro na API Gemini: HTTP %s - %s", resp.status_code, resp.text)
                return AIResponse(
                    content="",
                    is_success=False,
                    error_message=f"Falha na comunicação com o Google Gemini{detail}",
                )

        except httpx.TimeoutException:
            logger.error("Timeout na requisição para a API do Gemini (modelo: %s).", self.model_name)
            return AIResponse(
                content="",
                is_success=False,
                error_message="Tempo limite de resposta esgotado na comunicação com a API do Google Gemini. O servidor da Google demorou para responder. Por favor, tente enviar a pergunta novamente.",
            )
        except Exception as exc:
            logger.exception("Exceção inesperada ao consultar a API do Gemini: %s", exc)
            return AIResponse(
                content="",
                is_success=False,
                error_message=f"Erro ao conectar com a API do Gemini: {str(exc)}",
            )

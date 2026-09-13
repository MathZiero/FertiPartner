"""Cliente de integração com a API do Google Gemini (generateContent) com suporte a resiliência multi-modelos."""

import json
import logging
import os
import time
from typing import Any
import httpx

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole, ToolCall, ToolResult

logger = logging.getLogger(__name__)


def mask_secret(secret: str | None) -> str:
    """Mascara credenciais sensíveis para prevenir leakage em logs, traces e interfaces."""
    if not secret:
        return "None"
    clean = str(secret).strip()
    if len(clean) <= 8:
        return "***"
    return f"{clean[:4]}...{clean[-4:]}"


class GeminiClient:
    """Cliente HTTP resiliente para a API Google Gemini v1beta com failover em pool de quotas."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-3.5-flash-lite"
    DEFAULT_FALLBACK_MODELS = [
        "gemini-2.5-flash-lite",
        "gemini-3.0-flash",
        "gemini-3.1-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",

    ]

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        fallback_models: list[str] | None = None,
    ) -> None:
        self.api_key = (api_key if api_key is not None else self._resolve_env_key()).strip()
        self.model_name = (model_name or self.DEFAULT_MODEL).removeprefix("models/")
        if fallback_models is not None:
            self.fallback_models = [m.removeprefix("models/") for m in fallback_models]
        elif model_name is not None:
            self.fallback_models = [self.model_name]
        else:
            self.fallback_models = list(self.DEFAULT_FALLBACK_MODELS)

        self._http_client = httpx.Client(
            timeout=httpx.Timeout(90.0, connect=20.0, read=90.0, write=30.0)
        )

    @classmethod
    def _resolve_env_key(cls) -> str:
        """Resolve a chave do Gemini a partir do ambiente (.env local ou st.secrets em produção)."""
        try:
            if load_dotenv is not None:
                load_dotenv(override=False)
        except Exception:
            pass

        # 1. Verifica Streamlit Secrets (Produção no Streamlit Community Cloud)
        try:
            import streamlit as st
            for alias in ("GEMINI_API", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"):
                if alias in st.secrets:
                    val = str(st.secrets[alias]).strip().strip("\"'")
                    if val and len(val) > 10:
                        return val
        except Exception:
            pass

        # 2. Verifica variáveis de ambiente (.env ou SO)
        for alias in ("GEMINI_API", "GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY"):
            val = os.environ.get(alias, "").strip().strip("\"'")
            if val and len(val) > 10:
                return val

        return ""

    @classmethod
    def list_available_models(cls, api_key: str) -> list[str]:
        """Consulta a API do Google AI Studio para listar modelos disponíveis suportando generateContent.

        Prioriza o DEFAULT_MODEL e os modelos recomendados da série Gemini Flash.
        Retorna fallback seguro caso a API não responda ou a chave esteja ausente.
        """
        fallback = list(cls.DEFAULT_FALLBACK_MODELS)
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
                    deprecated_tokens = ["1.0", "1.5", "2.0", "gemini-2.5-flash", "gemini-2.5-pro", "vision", "text-bison", "chat-bison", "embedding", "aqa", "preview-tts"]
                    for m in models:
                        name = m.get("name", "").removeprefix("models/")
                        supported = m.get("supportedGenerationMethods", [])
                        if "generateContent" in supported and name.startswith("gemini-"):
                            if not any(dep in name for dep in deprecated_tokens):
                                valid_models.append(name)

                    if valid_models:
                        if cls.DEFAULT_MODEL in valid_models:
                            valid_models.remove(cls.DEFAULT_MODEL)
                            valid_models.insert(0, cls.DEFAULT_MODEL)
                        elif "gemini-3.6-flash" in valid_models:
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
                if msg.raw_parts:
                    # Preserva os parts originais exatos da Google (incluindo thoughtSignature e IDs)
                    contents.append({"role": "model", "parts": msg.raw_parts})
                else:
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
                        if tc.thought_signature:
                            call_obj["thoughtSignature"] = tc.thought_signature
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
        """Envia requisição para a API do Google Gemini com suporte a Function Calling e resiliência multi-modelos."""
        if not self.is_configured():
            return AIResponse(
                content="",
                is_success=False,
                error_message="Chave de API do Google Gemini não configurada. Insira sua chave para utilizar os recursos de IA.",
            )

        contents = self._convert_messages_to_gemini_contents(messages)
        if not contents:
            return AIResponse(content="", is_success=False, error_message="Nenhuma mensagem para envio.")

        # Constrói o pool de modelos para cascata resiliente
        models_cascade: list[str] = [self.model_name]
        for m in self.fallback_models:
            if m not in models_cascade:
                models_cascade.append(m)

        hit_quota_429 = False
        last_error_detail = ""

        for model_idx, current_model in enumerate(models_cascade):
            url = f"{self.BASE_URL}/{current_model}:generateContent?key={self.api_key}"

            gen_config: dict[str, Any] = {
                "maxOutputTokens": 2048,
            }
            # Na série Gemini 3.x, ativa thinkingLevel LOW para respostas ágeis sem timeout em chat
            if current_model.startswith("gemini-3"):
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

            has_more_models = model_idx < len(models_cascade) - 1
            max_retries = 2 if not has_more_models else 0
            switch_to_next_model = False

            for attempt in range(max_retries + 1):
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
                                model_used=current_model,
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
                                sig = (
                                    part.get("thoughtSignature")
                                    or part.get("thought_signature")
                                    or fc.get("thoughtSignature")
                                    or fc.get("thought_signature")
                                )
                                tool_calls.append(
                                    ToolCall(
                                        name=fc.get("name", ""),
                                        args=fc.get("args", {}),
                                        id=fc.get("id"),
                                        thought_signature=sig,
                                    )
                                )

                        finish_reason = first_candidate.get("finishReason", "STOP")
                        full_text = "".join(text_fragments).strip()

                        if current_model != self.model_name:
                            logger.info(
                                "Requisição Gemini atendida via modelo resiliente '%s' (após esgotamento/sobrecarga de '%s').",
                                current_model,
                                self.model_name,
                            )

                        return AIResponse(
                            content=full_text,
                            tool_calls=tool_calls,
                            is_success=True,
                            finish_reason=finish_reason,
                            raw_parts=parts,
                            model_used=current_model,
                        )

                    elif resp.status_code == 429:
                        hit_quota_429 = True
                        logger.warning(
                            "Modelo Gemini '%s' atingiu cota/rate limit (HTTP 429).",
                            current_model,
                        )
                        if has_more_models:
                            logger.info("Alternando para o próximo modelo do pool: '%s'...", models_cascade[model_idx + 1])
                            switch_to_next_model = True
                            break
                        else:
                            last_error_detail = "Limite de taxa (rate limit / cota gratuita) atingido na API do Gemini."
                            switch_to_next_model = True
                            break

                    elif resp.status_code == 503:
                        if attempt < max_retries:
                            wait_seconds = (attempt + 1) * 2.0
                            logger.warning(
                                "Gemini 503 (alta demanda temporária). Reenviando em %.1fs (tentativa %d/%d)...",
                                wait_seconds,
                                attempt + 1,
                                max_retries,
                            )
                            time.sleep(wait_seconds)
                            continue
                        if has_more_models:
                            logger.warning(
                                "Modelo '%s' sob alta demanda (HTTP 503). Alternando para próximo modelo '%s'...",
                                current_model,
                                models_cascade[model_idx + 1],
                            )
                            switch_to_next_model = True
                            break
                        else:
                            last_error_detail = (
                                f"O modelo '{current_model}' está temporariamente sob alta demanda nos servidores da Google (HTTP 503). "
                                "Aguarde alguns segundos ou selecione outro modelo (como gemini-3.8-flash) no seletor de modelos."
                            )
                            switch_to_next_model = True
                            break

                    elif resp.status_code == 404:
                        logger.warning("Modelo Gemini '%s' indisponível (HTTP 404).", current_model)
                        if has_more_models:
                            switch_to_next_model = True
                            break
                        err_data = resp.json().get("error", {})
                        err_msg = err_data.get("message", f"O modelo '{current_model}' não está disponível ou foi depreciado.")
                        last_error_detail = f"Modelo Gemini indisponível: {err_msg}"
                        switch_to_next_model = True
                        break

                    elif resp.status_code in (400, 401, 403):
                        err_data = resp.json().get("error", {})
                        err_msg = err_data.get("message", "Chave de API inválida ou parâmetros incorretos.")
                        logger.warning("Falha de autenticação/parâmetros no Gemini (%s): %s", mask_secret(self.api_key), err_msg)
                        return AIResponse(
                            content="",
                            is_success=False,
                            error_message=f"Erro no Google Gemini: {err_msg}",
                            model_used=current_model,
                        )

                    else:
                        err_msg = ""
                        try:
                            err_msg = resp.json().get("error", {}).get("message", "")
                        except Exception:
                            pass
                        detail = f": {err_msg}" if err_msg else f" (HTTP {resp.status_code})."
                        logger.error("Erro na API Gemini (%s): HTTP %s - %s", current_model, resp.status_code, resp.text)
                        if has_more_models:
                            switch_to_next_model = True
                            break
                        last_error_detail = f"Falha na comunicação com o Google Gemini{detail}"
                        switch_to_next_model = True
                        break

                except httpx.TimeoutException:
                    logger.warning("Timeout ao consultar modelo '%s'.", current_model)
                    if has_more_models:
                        switch_to_next_model = True
                        break
                    last_error_detail = "Tempo limite de resposta esgotado na comunicação com a API do Google Gemini. O servidor da Google demorou para responder. Por favor, tente enviar a pergunta novamente."
                    switch_to_next_model = True
                    break
                except Exception as exc:
                    logger.exception("Exceção inesperada no Gemini para modelo '%s': %s", current_model, exc)
                    if has_more_models:
                        switch_to_next_model = True
                        break
                    last_error_detail = f"Erro ao conectar com a API do Gemini: {str(exc)}"
                    switch_to_next_model = True
                    break

            if not switch_to_next_model:
                break

        if hit_quota_429:
            return AIResponse(
                content="",
                is_success=False,
                error_message=(
                    f"Limite de taxa ou cota gratuita esgotada nos modelos Gemini ({', '.join(models_cascade)}). "
                    "Aguarde alguns segundos ou utilize uma chave de API própria no seletor de modelos."
                ),
            )

        return AIResponse(
            content="",
            is_success=False,
            error_message=last_error_detail or "Não foi possível obter resposta da API do Gemini.",
        )

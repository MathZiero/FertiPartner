"""Orquestrador do FertiPartner.AI com ciclo de Function Calling / RAG."""

import logging
from typing import Any

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole, ToolCall, ToolResult
from app.domain.ai.guardrails import AIGuardrails
from app.domain.ai.prompts import SYSTEM_PROMPT_FERTIPARTNER_AI
from app.domain.ai.tools_schema import GEMINI_TOOLS_DECLARATIONS
from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class FertiPartnerAIOrchestrator:
    """Orquestra diálogos com a API do Gemini executando ferramentas do banco FertiPartner."""

    MAX_TOOL_TURNS = 4

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.client = gemini_client

    def ask(
        self,
        history: list[ChatMessage],
        user_prompt: str,
    ) -> tuple[AIResponse, list[ChatMessage]]:
        """Processa a mensagem do usuário executando chamadas de ferramenta se requisitado pelo Gemini."""
        if not self.client.is_configured():
            err_resp = AIResponse(
                content="",
                is_success=False,
                error_message="Chave da API do Google Gemini não configurada. Por favor, informe sua chave no painel lateral.",
            )
            return err_resp, history

        # 1. Validação de GuardRails (Prompt Injection, Jailbreak e Contenção de Escopo)
        guard_result = AIGuardrails.validate_input(user_prompt)
        if not guard_result.is_safe:
            working_history = list(history)
            working_history.append(ChatMessage(role=ChatRole.USER, content=user_prompt.strip()))
            message_text = guard_result.user_message or ""
            working_history.append(ChatMessage(role=ChatRole.MODEL, content=message_text))
            blocked_response = AIResponse(
                content=message_text,
                is_success=True,
                error_message=None,
            )
            return blocked_response, working_history

        # Cria uma cópia do histórico e adiciona a nova mensagem do usuário
        working_history = list(history)
        working_history.append(ChatMessage(role=ChatRole.USER, content=user_prompt.strip()))

        tools_used: list[str] = []
        response: AIResponse = AIResponse(content="", is_success=True)

        for turn in range(self.MAX_TOOL_TURNS):
            logger.info("Executando turno %d da conversa com Gemini", turn + 1)
            response = self.client.generate_content(
                messages=working_history,
                system_instruction=SYSTEM_PROMPT_FERTIPARTNER_AI,
                tools_declarations=GEMINI_TOOLS_DECLARATIONS,
            )

            if not response.is_success:
                return response, working_history

            # Se a LLM pediu chamadas de ferramentas:
            if response.tool_calls:
                # 1. Registra a resposta intermediária da IA com as tool_calls
                working_history.append(ChatMessage(
                    role=ChatRole.MODEL,
                    content=response.content,
                    tool_calls=response.tool_calls,
                    raw_parts=response.raw_parts,
                ))

                # 2. Executa cada ferramenta
                tool_results: list[ToolResult] = []
                for tc in response.tool_calls:
                    tools_used.append(tc.name)
                    logger.info("Executando ferramenta: %s com argumentos: %s", tc.name, tc.args)
                    exec_result = ToolExecutor.execute(tc.name, tc.args)
                    tool_results.append(ToolResult(name=tc.name, content=exec_result, id=tc.id))

                # 3. Adiciona os resultados ao histórico para reenvio
                working_history.append(ChatMessage(
                    role=ChatRole.TOOL,
                    content="",
                    tool_results=tool_results,
                ))
                # Continua o loop para a IA analisar os dados
                continue

            # Se não há mais tool calls, a IA concluiu sua resposta analítica
            final_message = ChatMessage(role=ChatRole.MODEL, content=response.content)
            working_history.append(final_message)
            response.tools_used = list(set(tools_used))
            return response, working_history

        # Se atingiu o limite de turnos de ferramentas sem parar
        return (
            AIResponse(
                content=response.content or "Consulta analítica processada.",
                is_success=True,
                tools_used=list(set(tools_used)),
            ),
            working_history,
        )

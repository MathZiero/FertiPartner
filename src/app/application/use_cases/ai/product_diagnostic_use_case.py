"""Caso de uso para geração de diagnóstico estratégico contextual por fertilizante."""

import json
from typing import Any

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole
from app.domain.ai.prompts import PRODUCT_DIAGNOSTIC_PROMPT_TEMPLATE, SYSTEM_PROMPT_FERTIPARTNER_AI
from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.tool_executor import ToolExecutor


class ProductDiagnosticUseCase:
    """Gera diagnóstico analítico de 3 pontos para a página de detalhes de um fertilizante."""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.client = gemini_client

    def execute(self, fertilizer_name: str) -> AIResponse:
        """Coleta o contexto estruturado do fertilizante e solicita o diagnóstico ao Gemini."""
        if not self.client.is_configured():
            return AIResponse(
                content="",
                is_success=False,
                error_message="Chave de API do Google Gemini não configurada.",
            )

        # 1. Coleta dados reais do banco para o produto
        spec = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": fertilizer_name})
        prices = ToolExecutor.execute("get_price_trends", {"fertilizer_name": fertilizer_name})
        flows = ToolExecutor.execute("get_trade_and_import_flows", {"fertilizer_name": fertilizer_name})
        balance = ToolExecutor.execute("get_brazil_supply_balance", {"fertilizer_name": fertilizer_name})

        product_context = json.dumps(
            {
                "especificacao": spec,
                "cotacoes_recentes": prices,
                "fluxos_importacao": flows,
                "balanco_nacional": balance,
            },
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = PRODUCT_DIAGNOSTIC_PROMPT_TEMPLATE.format(
            fertilizer_name=fertilizer_name,
            product_context=product_context,
        )

        messages = [ChatMessage(role=ChatRole.USER, content=user_prompt)]

        return self.client.generate_content(
            messages=messages,
            system_instruction=SYSTEM_PROMPT_FERTIPARTNER_AI,
            temperature=0.2,
        )

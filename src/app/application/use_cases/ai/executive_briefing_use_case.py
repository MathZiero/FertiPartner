"""Caso de uso para geração de briefing executivo semanal consolidado por IA."""

import json
import time

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole
from app.domain.ai.prompts import (
    EXECUTIVE_BRIEFING_PROMPT_TEMPLATE,
    SYSTEM_PROMPT_FERTIPARTNER_AI,
    get_briefing_date_ranges,
)
from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.tool_executor import ToolExecutor


class ExecutiveBriefingUseCase:
    """Gera o Briefing Semanal FertiPartner.AI com resumo da última semana e projeções da próxima semana."""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.client = gemini_client

    def execute(self) -> AIResponse:
        """Coleta notícias recentes e barômetros para síntese executiva da última e próxima semana."""
        if not self.client.is_configured():
            return AIResponse(
                content="",
                is_success=False,
                error_message="Chave de API do Google Gemini não configurada.",
            )

        news = ToolExecutor.execute("get_recent_news_7d", {"topic": "TODOS"})
        barometers = ToolExecutor.execute("get_market_sentiment_barometers", {})

        news_context = json.dumps(
            {
                "barometros_sentimento": barometers,
                "noticias_relevantes": news,
            },
            ensure_ascii=False,
            indent=2,
        )

        dates = get_briefing_date_ranges()
        user_prompt = EXECUTIVE_BRIEFING_PROMPT_TEMPLATE.format(
            current_date=dates["current_date"],
            past_week_range=dates["past_week_range"],
            future_week_range=dates["future_week_range"],
            news_context=news_context,
        )
        messages = [ChatMessage(role=ChatRole.USER, content=user_prompt)]

        return self.client.generate_content(
            messages=messages,
            system_instruction=SYSTEM_PROMPT_FERTIPARTNER_AI,
            temperature=0.2,
        )

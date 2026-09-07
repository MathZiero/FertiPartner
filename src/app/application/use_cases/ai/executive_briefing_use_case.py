"""Caso de uso para geração de briefing executivo semanal consolidado por IA."""

import json
from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole
from app.domain.ai.prompts import EXECUTIVE_BRIEFING_PROMPT_TEMPLATE, SYSTEM_PROMPT_FERTIPARTNER_AI
from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.tool_executor import ToolExecutor


class ExecutiveBriefingUseCase:
    """Gera o Briefing Semanal FertiPartner.AI consolidando notícias e barômetros de sentimento."""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.client = gemini_client

    def execute(self) -> AIResponse:
        """Coleta notícias dos últimos 7 dias e barômetros para síntese executiva."""
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
                "barometros_sentimento_7d": barometers,
                "noticias_relevantes_7d": news,
            },
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = EXECUTIVE_BRIEFING_PROMPT_TEMPLATE.format(news_context=news_context)
        messages = [ChatMessage(role=ChatRole.USER, content=user_prompt)]

        return self.client.generate_content(
            messages=messages,
            system_instruction=SYSTEM_PROMPT_FERTIPARTNER_AI,
            temperature=0.2,
        )

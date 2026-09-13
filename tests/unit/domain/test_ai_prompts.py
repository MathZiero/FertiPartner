"""Testes unitários rigorosos para prompts de sistema, personas e schemas de ferramentas de IA."""

import pytest
from app.domain.ai.prompts import (
    SYSTEM_PROMPT_FERTIPARTNER_AI,
    PRODUCT_DIAGNOSTIC_PROMPT_TEMPLATE,
    EXECUTIVE_BRIEFING_PROMPT_TEMPLATE,
)
from app.domain.ai.tools_schema import GEMINI_TOOLS_DECLARATIONS


class TestAIPromptsAndToolsSchema:
    """Validações de contrato e integridade dos prompts e esquemas de Function Calling."""

    def test_system_prompt_integrity(self):
        assert "FertiPartner.AI" in SYSTEM_PROMPT_FERTIPARTNER_AI
        assert "GROUNDING" in SYSTEM_PROMPT_FERTIPARTNER_AI
        assert "NUNCA invente cotações" in SYSTEM_PROMPT_FERTIPARTNER_AI
        assert "NUNCA utilize emojis" in SYSTEM_PROMPT_FERTIPARTNER_AI
        assert "CONTENÇÃO ESTRITA DE ESCOPO" in SYSTEM_PROMPT_FERTIPARTNER_AI

    def test_product_diagnostic_prompt_formatting(self):
        rendered = PRODUCT_DIAGNOSTIC_PROMPT_TEMPLATE.format(
            fertilizer_name="Fosfato Monoamônico (MAP)",
            product_context="Cotação atual: USD 580/t. Dependência: 74%.",
        )
        assert "Fosfato Monoamônico (MAP)" in rendered
        assert "Cotação atual: USD 580/t" in rendered
        assert "{fertilizer_name}" not in rendered
        assert "{product_context}" not in rendered

    def test_executive_briefing_prompt_formatting(self):
        from app.domain.ai.prompts import get_briefing_date_ranges

        dates = get_briefing_date_ranges()
        assert "current_date" in dates
        assert "past_week_range" in dates
        assert "future_week_range" in dates
        assert "/" in dates["current_date"]
        assert " a " in dates["past_week_range"]
        assert " a " in dates["future_week_range"]

        rendered = EXECUTIVE_BRIEFING_PROMPT_TEMPLATE.format(
            news_context="1. Fretes portuários em alta em Paranaguá.\n2. Safra de soja acelerada.",
        )
        assert "Briefing Semanal FertiPartner.AI" in rendered
        assert "RESUMO EXECUTIVO DA ÚLTIMA SEMANA" in rendered
        assert "O QUE ESPERAR PARA A PRÓXIMA SEMANA" in rendered
        assert dates["past_week_range"] in rendered
        assert dates["future_week_range"] in rendered
        assert "Fretes portuários em alta" in rendered
        assert "{news_context}" not in rendered

    def test_tools_schema_structure_and_types(self):
        assert isinstance(GEMINI_TOOLS_DECLARATIONS, list)
        assert len(GEMINI_TOOLS_DECLARATIONS) == 6

        tool_names = {t["name"] for t in GEMINI_TOOLS_DECLARATIONS}
        expected_names = {
            "get_fertilizer_technical_spec",
            "get_price_trends",
            "get_trade_and_import_flows",
            "get_brazil_supply_balance",
            "get_recent_news_7d",
            "get_market_sentiment_barometers",
        }
        assert tool_names == expected_names

        for tool in GEMINI_TOOLS_DECLARATIONS:
            assert "name" in tool and isinstance(tool["name"], str) and len(tool["name"]) > 0
            assert "description" in tool and isinstance(tool["description"], str) and len(tool["description"]) > 10
            assert "parameters" in tool and isinstance(tool["parameters"], dict)
            params = tool["parameters"]
            assert params.get("type") == "object"
            assert "properties" in params and isinstance(params["properties"], dict)

            # Se possui 'required', deve ser lista de strings contidas em 'properties'
            if "required" in params:
                assert isinstance(params["required"], list)
                for req in params["required"]:
                    assert req in params["properties"]

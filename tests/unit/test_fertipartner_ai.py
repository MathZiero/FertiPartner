"""Testes unitários para o FertiPartner.AI (Domínio, Infraestrutura e Casos de Uso)."""

import pytest
from unittest.mock import MagicMock, patch

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole, ToolCall
from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.tool_executor import ToolExecutor
from app.application.use_cases.ai.copilot_orchestrator import FertiPartnerAIOrchestrator
from app.application.use_cases.ai.product_diagnostic_use_case import ProductDiagnosticUseCase
from app.application.use_cases.ai.executive_briefing_use_case import ExecutiveBriefingUseCase


def test_gemini_client_unconfigured_fails_gracefully():
    """Garante que cliente sem chave informa erro claro e não trava a aplicação."""
    client = GeminiClient(api_key="")
    assert not client.is_configured()

    resp = client.generate_content(
        messages=[ChatMessage(role=ChatRole.USER, content="Olá")]
    )
    assert not resp.is_success
    assert "não configurada" in resp.error_message


def test_tool_executor_finds_technical_spec():
    """Valida execução da ferramenta de ficha técnica para Ureia e KCl."""
    res_ureia = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "Ureia"})
    assert res_ureia["status"] == "success"
    assert "CO(NH" in res_ureia["chemical_formula"]
    assert "46" in str(res_ureia["guarantees"])

    res_kcl = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "KCl"})
    assert res_kcl["status"] == "success"
    assert "Potássio" in res_kcl["fertilizer_name"]


def test_tool_executor_finds_price_trends():
    """Valida execução da ferramenta de cotações para Ureia."""
    res_prices = ToolExecutor.execute("get_price_trends", {"fertilizer_name": "Ureia"})
    assert res_prices["status"] == "success"
    assert len(res_prices["recent_prices"]) > 0
    first_price = res_prices["recent_prices"][0]
    assert "price_usd_per_mt" in first_price
    assert "benchmark" in first_price


def test_tool_executor_finds_supply_balance():
    """Valida execução da ferramenta de balanço nacional de abastecimento."""
    res_bal = ToolExecutor.execute("get_brazil_supply_balance", {"fertilizer_name": "Cloreto de Potássio"})
    assert res_bal["status"] == "success"
    assert len(res_bal["brazil_balances"]) > 0
    first = res_bal["brazil_balances"][0]
    assert "apparent_consumption_mt" in first
    assert "external_dependency_pct" in first


def test_tool_executor_finds_sentiment_barometers():
    """Valida execução da ferramenta de barômetros dos últimos 7 dias."""
    res_bar = ToolExecutor.execute("get_market_sentiment_barometers", {})
    assert res_bar["status"] == "success"
    assert len(res_bar["market_barometers"]) == 5


def test_copilot_orchestrator_executes_function_calling_loop():
    """Simula ciclo de Function Calling: IA pede tool, orquestrador executa e IA responde."""
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_configured.return_value = True

    # Turno 1: IA solicita tool_call para ficha técnica da Ureia
    resp_turn1 = AIResponse(
        content="",
        is_success=True,
        tool_calls=[ToolCall(name="get_fertilizer_technical_spec", args={"fertilizer_name": "Ureia"})],
    )
    # Turno 2: IA conclui com resposta em linguagem natural fundamentada
    resp_turn2 = AIResponse(
        content="A Ureia possui fórmula CO(NH₂)₂ e 46% de Nitrogênio de garantia.",
        is_success=True,
        tool_calls=[],
    )

    mock_client.generate_content.side_effect = [resp_turn1, resp_turn2]

    orchestrator = FertiPartnerAIOrchestrator(mock_client)
    final_resp, updated_history = orchestrator.ask(
        history=[],
        user_prompt="Qual a fórmula e teor da Ureia?",
    )

    assert final_resp.is_success
    assert "46% de Nitrogênio" in final_resp.content
    assert "get_fertilizer_technical_spec" in final_resp.tools_used
    assert mock_client.generate_content.call_count == 2
    # Histórico deve conter: USER -> MODEL (com tool call) -> TOOL (com resultado) -> MODEL (final)
    assert len(updated_history) == 4


def test_product_diagnostic_use_case_with_mock_client():
    """Garante que o caso de uso de diagnóstico compõe dados e invoca o Gemini."""
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_configured.return_value = True
    mock_client.generate_content.return_value = AIResponse(
        content="1. Preço: Estável. 2. Balanço: 91% dependência. 3. Ponto de Atenção: Volatilização.",
        is_success=True,
    )

    use_case = ProductDiagnosticUseCase(mock_client)
    resp = use_case.execute("Ureia")

    assert resp.is_success
    assert "91% dependência" in resp.content
    assert mock_client.generate_content.called


def test_executive_briefing_use_case_with_mock_client():
    """Garante que o caso de uso de briefing semanal compõe dados e invoca o Gemini."""
    mock_client = MagicMock(spec=GeminiClient)
    mock_client.is_configured.return_value = True
    mock_client.generate_content.return_value = AIResponse(
        content="1. Fretes: Gargalos moderados. 2. Preços: Cautela na safra. 3. Geopolítica: Estável.",
        is_success=True,
    )

    use_case = ExecutiveBriefingUseCase(mock_client)
    resp = use_case.execute()

    assert resp.is_success
    assert "Gargalos moderados" in resp.content
    assert mock_client.generate_content.called

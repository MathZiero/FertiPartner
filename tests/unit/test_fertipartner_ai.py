"""Testes unitários para o FertiPartner.AI (Domínio, Infraestrutura e Casos de Uso)."""

import pytest
from unittest.mock import MagicMock, patch

from app.domain.ai.entities import AIResponse, ChatMessage, ChatRole, ToolCall, ToolResult
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
    assert resp.error_message is not None
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


def test_gemini_client_default_model_is_gemini_3_6_flash():
    """Garante que o modelo padrão atualizado é o gemini-3.6-flash."""
    client = GeminiClient()
    assert client.DEFAULT_MODEL == "gemini-3.6-flash"
    assert client.model_name == "gemini-3.6-flash"


def test_gemini_client_list_available_models_fallback():
    """Valida retorno seguro de fallback quando a chave não estiver configurada."""
    models = GeminiClient.list_available_models("")
    assert "gemini-3.6-flash" in models
    assert "gemini-3.8-flash" in models


def test_gemini_client_list_available_models_with_mock_api():
    """Valida descoberta dinâmica de modelos via v1beta/models da Google."""
    mock_payload = {
        "models": [
            {
                "name": "models/gemini-1.5-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-2.5-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-3.8-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/gemini-3.6-flash",
                "supportedGenerationMethods": ["generateContent"],
            },
            {
                "name": "models/embedding-001",
                "supportedGenerationMethods": ["embedContent"],
            },
        ]
    }
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_get.return_value = mock_resp

        models = GeminiClient.list_available_models("AIzaSyFakeKeyTest12345")
        assert "gemini-3.6-flash" in models
        assert "gemini-3.8-flash" in models
        # Modelos depreciados e embeddings devem ter sido filtrados
        assert "gemini-1.5-flash" not in models
        assert "gemini-2.5-flash" not in models
        assert "embedding-001" not in models
        # gemini-3.6-flash deve ser o primeiro
        assert models[0] == "gemini-3.6-flash"


def test_gemini_client_handles_404_error_message():
    """Valida que resposta 404 da API Gemini extrai a mensagem detalhada da Google."""
    client = GeminiClient(api_key="AIzaSyFakeKeyTest12345", model_name="gemini-2.5-flash")
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {
            "error": {
                "code": 404,
                "message": "This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash.",
                "status": "NOT_FOUND",
            }
        }
        mock_resp.text = "404 Not Found"
        mock_post.return_value = mock_resp

        res = client.generate_content([ChatMessage(role=ChatRole.USER, content="Teste")])
        assert not res.is_success
        assert res.error_message is not None
        assert "gemini-3.6-flash" in res.error_message


def test_gemini_client_generation_config_omits_temperature_for_gemini_3():
    """Garante que para modelos da família gemini-3.x temperature não é enviada no payload."""
    client = GeminiClient(api_key="AIzaSyFakeKeyTest12345", model_name="gemini-3.6-flash")
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Resposta OK"}]}}]
        }
        mock_post.return_value = mock_resp

        res = client.generate_content(
            [ChatMessage(role=ChatRole.USER, content="Olá")],
            temperature=0.2,
        )
        assert res.is_success
        call_kwargs = mock_post.call_args[1]
        json_payload = call_kwargs["json"]
        assert "generationConfig" in json_payload
        assert "temperature" not in json_payload["generationConfig"]
        assert json_payload["generationConfig"]["maxOutputTokens"] == 2048
        assert json_payload["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "LOW"


def test_gemini_client_converts_tool_call_id_roundtrip():
    """Garante que id gerado na tool call é repassado na resposta de tool."""
    client = GeminiClient()
    msg_model = ChatMessage(
        role=ChatRole.MODEL,
        content="",
        tool_calls=[ToolCall(name="get_fertilizer_technical_spec", args={"fertilizer_name": "Ureia"}, id="call_abc_123")],
    )
    msg_tool = ChatMessage(
        role=ChatRole.TOOL,
        content="",
        tool_results=[ToolResult(name="get_fertilizer_technical_spec", content={"status": "ok"}, id="call_abc_123")],
    )

    contents = client._convert_messages_to_gemini_contents([msg_model, msg_tool])
    assert len(contents) == 2
    assert contents[0]["parts"][0]["functionCall"]["id"] == "call_abc_123"
    assert contents[1]["parts"][0]["functionResponse"]["id"] == "call_abc_123"


def test_gemini_client_preserves_thought_signature_and_raw_parts():
    """Garante que raw_parts e thoughtSignature retornados pela API são mantidos e reenviados."""
    client = GeminiClient(api_key="AIzaSyFakeKeyTest12345")
    mock_parts = [
        {
            "functionCall": {"name": "get_market_sentiment_barometers", "args": {}},
            "thoughtSignature": "CgcIARDA1wIYabcdef12345",
        }
    ]
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": mock_parts}, "finishReason": "STOP"}]
        }
        mock_post.return_value = mock_resp

        res = client.generate_content([ChatMessage(role=ChatRole.USER, content="Notícias")])
        assert res.is_success
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].thought_signature == "CgcIARDA1wIYabcdef12345"
        assert res.raw_parts == mock_parts

        # Valida que na conversão de histórico o raw_parts original com thoughtSignature é repassado intacto
        model_msg = ChatMessage(
            role=ChatRole.MODEL,
            content="",
            tool_calls=res.tool_calls,
            raw_parts=res.raw_parts,
        )
        converted = client._convert_messages_to_gemini_contents([model_msg])
        assert len(converted) == 1
        assert converted[0]["parts"] == mock_parts
        assert converted[0]["parts"][0]["thoughtSignature"] == "CgcIARDA1wIYabcdef12345"


def test_gemini_client_handles_503_retry_and_friendly_error():
    """Valida retentativas automáticas em erro 503 de alta demanda e mensagem explicativa final."""
    client = GeminiClient(api_key="AIzaSyFakeKeyTest12345", model_name="gemini-3.6-flash")
    with patch("httpx.Client.post") as mock_post, patch("time.sleep") as mock_sleep:
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = '{"error": {"code": 503, "message": "High demand"}}'
        mock_post.return_value = mock_resp

        res = client.generate_content([ChatMessage(role=ChatRole.USER, content="Teste")])
        assert not res.is_success
        assert res.error_message is not None
        assert "alta demanda" in res.error_message.lower()
        # Verifica que tentou 3 vezes (inicial + 2 retries)
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2




"""Testes unitários rigorosos para os casos de uso executivos do FertiPartner.AI."""

from unittest.mock import MagicMock, patch
import pytest

from app.application.use_cases.ai.product_diagnostic_use_case import ProductDiagnosticUseCase
from app.application.use_cases.ai.executive_briefing_use_case import ExecutiveBriefingUseCase
from app.domain.ai.entities import AIResponse


class TestUseCasesStrict:
    """Validações de contrato e resiliência dos casos de uso de IA."""

    def test_product_diagnostic_unconfigured_client(self):
        client = MagicMock()
        client.is_configured.return_value = False
        use_case = ProductDiagnosticUseCase(client)

        resp = use_case.execute("Ureia")
        assert resp.is_success is False
        assert "não configurada" in resp.error_message
        client.generate_content.assert_not_called()

    def test_product_diagnostic_successful_execution(self):
        client = MagicMock()
        client.is_configured.return_value = True
        client.generate_content.return_value = AIResponse(
            content="Diagnóstico Ureia: Mercado estável, 97% de dependência externa, atenção à volatilização.",
            is_success=True,
        )

        use_case = ProductDiagnosticUseCase(client)
        with patch("app.application.use_cases.ai.product_diagnostic_use_case.ToolExecutor.execute") as mock_tool:
            mock_tool.return_value = {"status": "success", "data": "dummy"}

            resp = use_case.execute("Ureia")

            assert resp.is_success is True
            assert "Diagnóstico Ureia" in resp.content
            assert client.generate_content.call_count == 1
            # Deve ter executado as 4 ferramentas contextuais
            assert mock_tool.call_count == 4

    def test_executive_briefing_unconfigured_client(self):
        client = MagicMock()
        client.is_configured.return_value = False
        use_case = ExecutiveBriefingUseCase(client)

        resp = use_case.execute()
        assert resp.is_success is False
        assert "não configurada" in resp.error_message
        client.generate_content.assert_not_called()

    def test_executive_briefing_successful_execution(self):
        client = MagicMock()
        client.is_configured.return_value = True
        client.generate_content.return_value = AIResponse(
            content="Briefing Semanal: Fretes marítimos estáveis, compras aquecidas para safrinha.",
            is_success=True,
        )

        use_case = ExecutiveBriefingUseCase(client)
        with patch("app.application.use_cases.ai.executive_briefing_use_case.ToolExecutor.execute") as mock_tool:
            mock_tool.return_value = {"status": "success"}

            resp = use_case.execute()

            assert resp.is_success is True
            assert "Briefing Semanal" in resp.content
            assert client.generate_content.call_count == 1
            # Deve ter executado notícias e barômetros
            assert mock_tool.call_count == 2

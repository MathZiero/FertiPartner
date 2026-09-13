"""Testes ponta a ponta (E2E) para os módulos analíticos, de inteligência e observabilidade."""

import pytest
from tests.e2e.pages.dashboard_page import DashboardPage


class TestE2EInteractiveModules:
    """Validação dos módulos interativos avançados da plataforma."""

    def test_comparative_analytics_module_and_charts(self, driver, app_url):
        """Valida a Central de Análise Comparativa Multidimensional NPK."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("analises-comparativas")

        page.assert_no_streamlit_exceptions()

        # Verifica módulos analíticos
        headers = page.get_headers()
        header_text = " ".join(headers).lower()
        assert "análise comparativa" in header_text or "preços" in header_text

        # Verifica que múltiplos gráficos Plotly foram renderizados
        charts = page.count_plotly_charts()
        assert charts >= 2, f"Esperado ao menos 2 gráficos Plotly em analises-comparativas, encontrado {charts}"

    def test_market_news_and_sentiment_barometers(self, driver, app_url):
        """Valida o Radar de Notícias NPK e barômetros de sentimento de mercado."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("noticias-mercado")

        page.assert_no_streamlit_exceptions()
        headers = page.get_headers()
        header_text = " ".join(headers).lower()
        assert "notícias" in header_text or "radar" in header_text

    def test_observability_and_system_health(self, driver, app_url):
        """Valida o painel de observabilidade, integridade do banco e histórico de execuções."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("observabilidade")

        page.assert_no_streamlit_exceptions()
        headers = page.get_headers()
        assert len(headers) >= 1

    def test_software_architecture_documentation(self, driver, app_url):
        """Valida a página de documentação da arquitetura de software (C4, camadas Clean Arch)."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("software")

        page.assert_no_streamlit_exceptions()
        headers = page.get_headers()
        header_text = " ".join(headers).lower()
        assert "software" in header_text or "arquitetura" in header_text

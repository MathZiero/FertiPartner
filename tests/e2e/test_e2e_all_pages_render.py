"""Testes ponta a ponta (E2E) com Selenium validando a renderização de 100% das páginas da aplicação."""

import pytest
from tests.e2e.pages.dashboard_page import DashboardPage


class TestE2EAllPagesRender:
    """Valida que cada uma das rotas oficiais carrega perfeitamente sem erros ou exceções no DOM."""

    @pytest.mark.parametrize(
        "route_path",
        [
            # Visão Geral & Documentação
            "",
            "inicio",
            "readme",
            # Primários: Nitrogenados
            "fert-ureia",
            "fert-amonia-anidra",
            "fert-nitrato-de-amonio",
            "fert-sulfato-de-amonio",
            # Primários: Fosfatados
            "fert-map",
            "fert-dap",
            "fert-ssp",
            "fert-tsp",
            "fert-rocha-fosfatica",
            # Primários: Potássicos
            "fert-cloreto-de-potassio",
            "fert-sulfato-de-potassio",
            # Secundários & Micronutrientes
            "fert-enxofre-elementar",
            "fert-micronutrientes",
            # Inteligência & Infraestrutura
            "analises-comparativas",
            "noticias-mercado",
            "fertipartner-ai",
            "observabilidade",
            "software",
        ],
    )
    def test_page_renders_cleanly_without_exceptions(self, driver, app_url, route_path):
        """Acessa a rota, aguarda a hidratação e garante ausência de falhas técnicas."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url(route_path)

        # 1. Validação estrita: Nenhuma exceção Python no DOM
        page.assert_no_streamlit_exceptions()

        # 2. Validação estrutural: Cabeçalhos presentes
        headers = page.get_headers()
        assert len(headers) >= 1, f"Rota '{route_path}' não renderizou nenhum cabeçalho no DOM."

        # 3. Título da página do navegador deve ser o oficial do FertiPartner
        assert "FertiPartner" in driver.title

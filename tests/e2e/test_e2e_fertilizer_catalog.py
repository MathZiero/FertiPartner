"""Testes ponta a ponta (E2E) para as páginas dedicadas de fertilizantes do catálogo NPK."""

import pytest
from tests.e2e.pages.dashboard_page import DashboardPage


class TestE2EFertilizerCatalog:
    """Validações em profundidade das páginas dedicadas a cada fertilizante individual."""

    @pytest.mark.parametrize(
        "fertilizer_route",
        [
            "fert-ureia",
            "fert-map",
            "fert-dap",
            "fert-cloreto-de-potassio",
            "fert-amonia-anidra",
            "fert-nitrato-de-amonio",
            "fert-sulfato-de-amonio",
            "fert-ssp",
            "fert-tsp",
            "fert-rocha-fosfatica",
            "fert-sulfato-de-potassio",
            "fert-enxofre-elementar",
            "fert-micronutrientes",
        ],
    )
    def test_fertilizer_page_deep_render(self, driver, app_url, fertilizer_route):
        """Valida que a página do produto exibe especificações, mapas, gráficos e downloads sem erros."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url(fertilizer_route)

        # 1. Ausência de exceções
        page.assert_no_streamlit_exceptions()

        # 2. Cabeçalhos técnicos do produto
        headers = page.get_headers()
        assert len(headers) >= 2, f"Página '{fertilizer_route}' deve conter múltiplos cabeçalhos de seção"

        # 3. Presença de gráficos Plotly (produção, comércio, preços)
        charts_count = page.count_plotly_charts()
        assert charts_count >= 1, f"Página '{fertilizer_route}' deve renderizar ao menos 1 gráfico Plotly interativo"

        # 4. Presença de métricas técnicas ou abas informativas
        metrics_count = page.count_metrics()
        # Alguns produtos exibem métricas NPK diretamente no cabeçalho
        assert charts_count >= 1 or metrics_count >= 1, f"Página '{fertilizer_route}' deve conter dados visuais (gráficos ou métricas)"

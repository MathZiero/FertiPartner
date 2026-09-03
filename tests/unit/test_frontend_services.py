"""Testes unitários para os serviços, componentes e temas do front-end Streamlit."""

import pytest
import pandas as pd
import plotly.graph_objects as go

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.theme import (
    apply_ferti_theme,
    format_metric_tons,
    format_currency_usd,
    get_default_plotly_config,
)
from app.presentation.streamlit.views import (
    view_market_overview,
    view_fertilizers_catalog,
    view_global_production,
    view_international_trade,
    view_trade_flows_sankey,
    view_price_benchmarks,
    view_brazil_market,
    view_comparative_analytics,
    view_system_health,
)


def test_theme_formatters():
    """Testa formatação de moedas e unidades métricas."""
    assert format_metric_tons(1_500_000) == "1.50 M MT"
    assert format_metric_tons(2_500) == "2.5 k MT"
    assert format_metric_tons(450) == "450.0 MT"
    assert format_metric_tons(0) == "0 MT"

    assert format_currency_usd(1_200_000_000) == "$ 1.20 B"
    assert format_currency_usd(4_500_000) == "$ 4.50 M"
    assert format_currency_usd(2_500) == "$ 2.5 k"
    assert format_currency_usd(120.5) == "$ 120.50"
    assert format_currency_usd(0) == "$ 0,00"


def test_apply_ferti_theme():
    """Valida aplicação do tema AgTech no objeto Figure do Plotly."""
    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[10, 20])])
    themed_fig = apply_ferti_theme(fig, title="Teste Tema", height=350)
    layout = themed_fig.layout
    assert isinstance(layout, go.Layout)
    assert layout.template is not None
    assert layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert layout.height == 350

    cfg = get_default_plotly_config()
    assert cfg.get("responsive") is True
    assert cfg.get("displaylogo") is False


def test_data_service_fertilizer_profiles():
    """Valida retorno do DataFrame de perfis de fertilizantes."""
    df = FertiDataService.get_fertilizer_profiles()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "canonical_name" in df.columns
    assert "chemical_formula" in df.columns
    assert "cas_rn" in df.columns


def test_data_service_global_production():
    """Valida dados do ranking de produção global."""
    df = FertiDataService.get_global_production_rankings()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "country_name" in df.columns
    assert "standard_quantity_mt" in df.columns
    assert "global_market_share_pct" in df.columns


def test_data_service_bilateral_trade():
    """Valida dados de fluxos de comércio bilateral."""
    df = FertiDataService.get_bilateral_trade_flows()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "exporter_country" in df.columns
    assert "importer_country" in df.columns
    assert "total_quantity_mt" in df.columns


def test_data_service_brazil_dependency():
    """Valida indicadores de dependência externa do Brasil."""
    df = FertiDataService.get_brazil_external_dependency()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "fertilizer_name" in df.columns
    assert "external_dependency_pct" in df.columns
    assert "apparent_consumption_mt" in df.columns


def test_data_service_price_trends():
    """Valida séries temporais de preços e benchmarks."""
    df = FertiDataService.get_price_benchmark_trends()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "standard_price_usd_per_mt" in df.columns
    assert "benchmark_name" in df.columns


def test_data_service_brazil_uf_distribution():
    """Valida estimativa e distribuição do consumo por estado (UF)."""
    df = FertiDataService.get_brazil_uf_distribution()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "uf" in df.columns
    assert "share_pct" in df.columns


def test_data_service_audit_runs():
    """Valida histórico recente de execuções de auditoria."""
    df = FertiDataService.get_audit_runs()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "source_name" in df.columns
    assert "source_code" in df.columns
    assert "status" in df.columns
    assert "records_count" in df.columns


def test_views_have_render_view_callable():
    """Garante que todas as 9 páginas implementam render_view() chamável."""
    views = [
        view_market_overview,
        view_fertilizers_catalog,
        view_global_production,
        view_international_trade,
        view_trade_flows_sankey,
        view_price_benchmarks,
        view_brazil_market,
        view_comparative_analytics,
        view_system_health,
    ]
    for v in views:
        assert hasattr(v, "render_view"), f"{v.__name__} não possui render_view"
        assert callable(v.render_view), f"{v.__name__}.render_view não é chamável"

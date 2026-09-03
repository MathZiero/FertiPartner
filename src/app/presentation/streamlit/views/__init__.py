"""Vistas e páginas analíticas do FertiPartner."""

from app.presentation.streamlit.views import (
    v01_market_overview as view_market_overview,
    v02_fertilizers_catalog as view_fertilizers_catalog,
    v03_global_production as view_global_production,
    v04_international_trade as view_international_trade,
    v05_trade_flows_sankey as view_trade_flows_sankey,
    v06_price_benchmarks as view_price_benchmarks,
    v07_brazil_market as view_brazil_market,
    v08_comparative_analytics as view_comparative_analytics,
    v09_system_health as view_system_health,
)

__all__ = [
    "view_market_overview",
    "view_fertilizers_catalog",
    "view_global_production",
    "view_international_trade",
    "view_trade_flows_sankey",
    "view_price_benchmarks",
    "view_brazil_market",
    "view_comparative_analytics",
    "view_system_health",
]

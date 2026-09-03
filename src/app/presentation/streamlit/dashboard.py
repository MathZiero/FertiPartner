"""Aplicação Principal Streamlit do FertiPartner com navegação moderna (st.navigation)."""

import sys
from pathlib import Path

# Garante que a pasta src esteja no sys.path para resolução consistente dos módulos da aplicação
_src_dir = str(Path(__file__).resolve().parents[3])
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

from app.presentation.streamlit.styles import inject_custom_styles
from app.presentation.streamlit.services.data_service import FertiDataService
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

# Configuração global da página
st.set_page_config(
    page_title="FertiPartner • Inteligência de Mercado NPK",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção das regras de design do tema AgTech
inject_custom_styles()

# Estrutura moderna de navegação por seções declarativas (Streamlit 1.36+)
pages = {
    "🌐 Mercado & Visão Geral": [
        st.Page(
            view_market_overview.render_view,
            title="Visão Geral",
            icon=":material/dashboard:",
            default=True,
            url_path="visao-geral",
        ),
        st.Page(
            view_fertilizers_catalog.render_view,
            title="Catálogo de Fertilizantes",
            icon=":material/science:",
            url_path="catalogo",
        ),
    ],
    "🏭 Produção & Comércio": [
        st.Page(
            view_global_production.render_view,
            title="Produção Global",
            icon=":material/factory:",
            url_path="producao-global",
        ),
        st.Page(
            view_international_trade.render_view,
            title="Comércio Internacional",
            icon=":material/public:",
            url_path="comercio-internacional",
        ),
        st.Page(
            view_trade_flows_sankey.render_view,
            title="Fluxos Comerciais (Sankey)",
            icon=":material/swap_calls:",
            url_path="fluxos-sankey",
        ),
    ],
    "📈 Preços & Inteligência": [
        st.Page(
            view_price_benchmarks.render_view,
            title="Preços & Benchmarks",
            icon=":material/trending_up:",
            url_path="precos-benchmarks",
        ),
        st.Page(
            view_brazil_market.render_view,
            title="Mercado Brasileiro",
            icon=":material/flag:",
            url_path="mercado-brasil",
        ),
        st.Page(
            view_comparative_analytics.render_view,
            title="Análises & Comparações",
            icon=":material/analytics:",
            url_path="analises-comparativas",
        ),
    ],
    "⚙️ Infraestrutura": [
        st.Page(
            view_system_health.render_view,
            title="Auditoria & Fontes 4NF",
            icon=":material/dns:",
            url_path="auditoria-sistema",
        ),
    ],
}

# Inicialização da navegação
pg = st.navigation(pages)

# Renderização da barra lateral com branding corporativo
with st.sidebar:
    st.markdown(
        """
        <div class="fp-brand-container">
            <div class="fp-brand-title">
                <span>🌱 Ferti</span><span class="fp-brand-accent">Partner</span>
            </div>
            <div class="fp-brand-tagline">Inteligência de Mercado NPK</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status de conectividade com o Supabase
    is_connected = FertiDataService.check_connection()
    status_text = "Supabase 4NF Ativo" if is_connected else "Modo Resiliente"
    status_color = "#10B981" if is_connected else "#F59E0B"
    st.markdown(
        f"""
        <div style="margin-bottom: 1.2rem; padding: 0 0.5rem;">
            <div class="fp-status-pill" style="border-color: {status_color}40; background: {status_color}15; color: {status_color};">
                <div class="fp-status-dot" style="background-color: {status_color}; box-shadow: 0 0 8px {status_color};"></div>
                <span>{status_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Rodapé da barra lateral
    st.markdown(
        """
        <div style="position: fixed; bottom: 12px; font-size: 0.72rem; color: #475569; padding-left: 0.5rem;">
            FertiPartner v0.1.0 • Streamlit 1.63 • 4NF
        </div>
        """,
        unsafe_allow_html=True,
    )

# Execução da página selecionada
pg.run()

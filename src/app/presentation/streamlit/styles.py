"""Estilos CSS personalizados e design system AgTech (Light Mode) para o FertiPartner."""

import streamlit as st

CUSTOM_CSS = """
<style>
/* Importação de fontes modernas do Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Regras globais de tipografia em Modo Claro */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #1F2937;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: #1B4332;
}

/* Centralização obrigatória de todos os títulos principais */
h1, .stApp h1, [data-testid="stHeader"] h1 {
    text-align: center !important;
    width: 100% !important;
}

/* Espaçamento e layout do container principal */
.block-container {
    padding-top: 1.75rem !important;
    padding-bottom: 3rem !important;
    max-width: 96% !important;
}

/* Forçar Modo Claro na Barra Lateral e em todos os seus containers internos */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarHeader"] {
    background-color: #F3F6F4 !important;
    background: #F3F6F4 !important;
    border-right: 1px solid #E2E8F0 !important;
    color: #1F2937 !important;
}

/* Logo no cabeçalho nativo da sidebar */
[data-testid="stSidebarHeader"] {
    padding-top: 1.25rem !important;
    padding-bottom: 0.75rem !important;
    border-bottom: 1px solid #E2E8F0 !important;
}

[data-testid="stSidebarHeader"] img {
    max-height: 48px !important;
    width: auto !important;
}

/* Textos e ícones da navegação na barra lateral */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
    color: #1F2937 !important;
}

/* Itens da navegação */
[data-testid="stSidebarNavItems"] a {
    color: #374151 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.75rem !important;
}

[data-testid="stSidebarNavItems"] a:hover {
    background-color: #E5EAE7 !important;
    color: #1B4332 !important;
}

[data-testid="stSidebarNavItems"] a[aria-current="page"] {
    background-color: #D8F3DC !important;
    color: #1B4332 !important;
    font-weight: 700 !important;
}

/* Separadores de seção da sidebar */
[data-testid="stSidebarNavSeparator"] {
    border-color: #E2E8F0 !important;
    margin: 0.5rem 0 !important;
}

/* Títulos de categorias da barra lateral */
[data-testid="stSidebarNavItems"] span[data-testid="stSidebarNavHeader"] {
    color: #52796F !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Header estilizado centralizado */
.fp-header-container {
    background: linear-gradient(135deg, #FFFFFF 0%, #F0F7F3 100%);
    border: 1px solid #D8F3DC;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    text-align: center;
}

.fp-header-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    color: #1B4332 !important;
    text-align: center !important;
}

.fp-header-subtitle {
    font-size: 0.95rem;
    color: #4B5563 !important;
    margin-top: 0.4rem;
    margin-bottom: 0;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    text-align: center !important;
}

/* Cards e containers com borda em Modo Claro */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border-radius: 12px !important;
    border: 1px solid #E5EAE7 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
}

/* Badges e Pílulas */
.fp-badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

.fp-badge-emerald {
    background: #D8F3DC;
    color: #2D6A4F;
    border: 1px solid #B7E4C7;
}

.fp-badge-blue {
    background: #DBEAFE;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
}

.fp-badge-amber {
    background: #FEF3C7;
    color: #B45309;
    border: 1px solid #FDE68A;
}

.fp-badge-purple {
    background: #EDE9FE;
    color: #6D28D9;
    border: 1px solid #DDD6FE;
}

/* Tabs modernas em fundo claro */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #EDF3EF;
    padding: 6px;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #4B5563 !important;
    font-weight: 500;
    padding: 8px 16px;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #2D6A4F !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

/* Rodapé sutil */
.fp-footer {
    text-align: center;
    font-size: 0.8rem;
    color: #6B7280;
    padding: 2rem 0 1rem 0;
    border-top: 1px solid #E5EAE7;
    margin-top: 3rem;
}
</style>
"""


def inject_custom_styles() -> None:
    """Injeta as regras CSS do design system AgTech (Modo Claro) na aplicação."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

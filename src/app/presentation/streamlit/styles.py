"""Estilos CSS personalizados e design system AgTech para o FertiPartner."""

import streamlit as st

CUSTOM_CSS = """
<style>
/* Importação de fontes modernas do Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Regras globais de tipografia */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #F1F5F9;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* Redução sutil de margem do topo da página */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 96% !important;
}

/* Barra lateral estilizada */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1424 0%, #080D18 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Header estilizado */
.fp-header-container {
    background: linear-gradient(135deg, rgba(19, 28, 46, 0.7) 0%, rgba(16, 185, 129, 0.08) 100%);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}

.fp-header-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(90deg, #FFFFFF 0%, #E2E8F0 60%, #10B981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.fp-header-subtitle {
    font-size: 0.95rem;
    color: #94A3B8;
    margin-top: 0.4rem;
    margin-bottom: 0;
}

/* Cards de Métricas Premium */
.fp-kpi-card {
    background: linear-gradient(145deg, #131C2E 0%, #0E1626 100%);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease-in-out;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.fp-kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(16, 185, 129, 0.4);
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.12);
}

.fp-kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #10B981 0%, #059669 100%);
    border-radius: 4px 0 0 4px;
}

.fp-kpi-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94A3B8;
    margin-bottom: 0.5rem;
}

.fp-kpi-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.1;
    margin-bottom: 0.4rem;
}

.fp-kpi-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
}

.fp-delta-positive {
    color: #10B981;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
}

.fp-delta-negative {
    color: #F43F5E;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
}

.fp-delta-neutral {
    color: #94A3B8;
    font-weight: 500;
}

/* Badges e Tags */
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
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.fp-badge-blue {
    background: rgba(59, 130, 246, 0.15);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.fp-badge-amber {
    background: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.fp-badge-purple {
    background: rgba(139, 92, 246, 0.15);
    color: #A78BFA;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

/* Estilo para containers de gráficos */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #111827 !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Customização de Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #0E1626;
    padding: 6px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94A3B8 !important;
    font-weight: 500;
    padding: 8px 16px;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background-color: #1E293B !important;
    color: #10B981 !important;
    font-weight: 700 !important;
}

/* Estilização da marca no sidebar */
.fp-brand-container {
    padding: 1rem 0.5rem 1.5rem 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 1rem;
}

.fp-brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.fp-brand-accent {
    color: #10B981;
}

.fp-brand-tagline {
    font-size: 0.75rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* Status Pill */
.fp-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(16, 185, 129, 0.1);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.25);
    margin-top: 0.5rem;
}

.fp-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
}

/* Rodapé elegante */
.fp-footer {
    text-align: center;
    font-size: 0.78rem;
    color: #64748B;
    padding: 2rem 0 1rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin-top: 3rem;
}
</style>
"""


def inject_custom_styles() -> None:
    """Injeta as regras CSS do design system AgTech na página atual."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

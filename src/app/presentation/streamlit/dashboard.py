"""Aplicação Principal Streamlit do FertiPartner com navegação moderna e estrutura de páginas."""

import sys
from pathlib import Path

# Garante que a pasta src esteja no sys.path para resolução consistente dos módulos da aplicação
_src_dir = str(Path(__file__).resolve().parents[3])
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

from app.presentation.streamlit.styles import inject_custom_styles
from app.presentation.streamlit.services.data_service import FertiDataService

# Configuração global da página
st.set_page_config(
    page_title="FertiPartner • Inteligência de Mercado NPK",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção das regras de design do tema AgTech
inject_custom_styles()

def _find_pages_dir() -> Path:
    """Localiza o diretório de páginas do Streamlit independentemente de como o script foi invocado."""
    candidates = [
        Path(__file__).resolve().parent / "pages",
        Path(__file__).resolve().parent / "src" / "app" / "presentation" / "streamlit" / "pages",
        Path.cwd() / "src" / "app" / "presentation" / "streamlit" / "pages",
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "01_visao_geral.py").is_file():
            return candidate.resolve()

    current = Path(__file__).resolve().parent
    while current.parent != current:
        candidate = current / "src" / "app" / "presentation" / "streamlit" / "pages"
        if candidate.is_dir() and (candidate / "01_visao_geral.py").is_file():
            return candidate.resolve()
        current = current.parent

    raise FileNotFoundError("Diretório de páginas do Streamlit não encontrado.")


PAGES_DIR = _find_pages_dir()

# Estrutura moderna de navegação por arquivos de página isolados (Streamlit 1.36+)
pages = {
    "🌐 Mercado & Visão Geral": [
        st.Page(
            str(PAGES_DIR / "01_visao_geral.py"),
            title="Visão Geral",
            icon=":material/dashboard:",
            default=True,
            url_path="visao-geral",
        ),
        st.Page(
            str(PAGES_DIR / "02_catalogo.py"),
            title="Catálogo de Fertilizantes",
            icon=":material/science:",
            url_path="catalogo",
        ),
    ],
    "🏭 Produção & Comércio": [
        st.Page(
            str(PAGES_DIR / "03_producao_global.py"),
            title="Produção Global",
            icon=":material/factory:",
            url_path="producao-global",
        ),
        st.Page(
            str(PAGES_DIR / "04_comercio_internacional.py"),
            title="Comércio Internacional",
            icon=":material/public:",
            url_path="comercio-internacional",
        ),
        st.Page(
            str(PAGES_DIR / "05_fluxos_sankey.py"),
            title="Fluxos Comerciais (Sankey)",
            icon=":material/swap_calls:",
            url_path="fluxos-sankey",
        ),
    ],
    "📈 Preços & Inteligência": [
        st.Page(
            str(PAGES_DIR / "06_precos_benchmarks.py"),
            title="Preços & Benchmarks",
            icon=":material/trending_up:",
            url_path="precos-benchmarks",
        ),
        st.Page(
            str(PAGES_DIR / "07_mercado_brasil.py"),
            title="Mercado Brasileiro",
            icon=":material/flag:",
            url_path="mercado-brasil",
        ),
        st.Page(
            str(PAGES_DIR / "08_analises_comparativas.py"),
            title="Análises & Comparações",
            icon=":material/analytics:",
            url_path="analises-comparativas",
        ),
    ],
    "🌱 Sazonalidade & Safras": [
        st.Page(
            str(PAGES_DIR / "10_sazonalidade.py"),
            title="Sazonalidade das Safras",
            icon=":material/calendar_month:",
            url_path="sazonalidade",
        ),
    ],
    "💡 Inteligência & Alertas": [
        st.Page(
            str(PAGES_DIR / "11_insights_mercado.py"),
            title="Insights de Mercado",
            icon=":material/lightbulb:",
            url_path="insights-mercado",
        ),
    ],
    "⚙️ Infraestrutura": [
        st.Page(
            str(PAGES_DIR / "09_auditoria_sistema.py"),
            title="Auditoria & Fontes 4NF",
            icon=":material/dns:",
            url_path="auditoria-sistema",
        ),
    ],
}

# Inicialização da navegação
pg = st.navigation(pages)

# Renderização da barra lateral com branding e status nativo
with st.sidebar:
    st.title("🌱 FertiPartner")
    st.caption("Inteligência de Mercado NPK")
    st.divider()

    # Status de conectividade com o Supabase
    is_connected = FertiDataService.check_connection()
    if is_connected:
        st.success("🟢 Supabase 4NF Conectado", icon="✅")
    else:
        st.warning("🟠 Modo Resiliente Ativo", icon="⚠️")

    st.divider()
    st.caption("FertiPartner v0.1.0 • Streamlit 1.63 • 4NF")

# Execução da página selecionada
pg.run()

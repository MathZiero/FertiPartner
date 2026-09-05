"""Aplicação Principal Streamlit do FertiPartner com navegação moderna e tema AgTech Light Mode."""

import sys
import importlib
from pathlib import Path

# Garante que a pasta src esteja no sys.path para resolução consistente dos módulos da aplicação
_src_dir = str(Path(__file__).resolve().parents[3])
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Força recarregamento dinâmico dos módulos de apresentação para aplicar imediatamente CSS, temas e componentes
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("app.presentation.streamlit.") and not mod_name.endswith(".dashboard"):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

import streamlit as st

from app.presentation.streamlit.styles import inject_custom_styles

# Configuração global da página
st.set_page_config(
    page_title="FertiPartner • Inteligência de Mercado NPK",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção das regras de design do tema AgTech (Modo Claro)
inject_custom_styles()

# Logo oficial no topo da barra lateral (como o logo de um site)
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.svg"
if LOGO_PATH.is_file():
    st.logo(str(LOGO_PATH), size="large")


def _find_pages_dir() -> Path:
    """Localiza o diretório de páginas do Streamlit independentemente de como o script foi invocado."""
    candidates = [
        Path(__file__).resolve().parent / "pages",
        Path(__file__).resolve().parent / "src" / "app" / "presentation" / "streamlit" / "pages",
        Path.cwd() / "src" / "app" / "presentation" / "streamlit" / "pages",
    ]
    for candidate in candidates:
        if candidate.is_dir() and ((candidate / "01_inicio.py").is_file() or (candidate / "01_visao_geral.py").is_file()):
            return candidate.resolve()

    current = Path(__file__).resolve().parent
    while current.parent != current:
        candidate = current / "src" / "app" / "presentation" / "streamlit" / "pages"
        if candidate.is_dir() and ((candidate / "01_inicio.py").is_file() or (candidate / "01_visao_geral.py").is_file()):
            return candidate.resolve()
        current = current.parent

    raise FileNotFoundError("Diretório de páginas do Streamlit não encontrado.")


PAGES_DIR = _find_pages_dir()

# Estrutura moderna de navegação organizada por categorias singulares
pages = {
    "🌐 Visão Geral": [
        st.Page(
            str(PAGES_DIR / "01_inicio.py"),
            title="Início",
            icon=":material/home:",
            default=True,
            url_path="inicio",
        ),
        st.Page(
            str(PAGES_DIR / "02_catalogo.py"),
            title="Catálogo de Fertilizantes",
            icon=":material/science:",
            url_path="catalogo",
        ),
    ],
    "🏭 Produção": [
        st.Page(
            str(PAGES_DIR / "03_producao_global.py"),
            title="Produção Global",
            icon=":material/factory:",
            url_path="producao-global",
        ),
    ],
    "🚢 Comércio": [
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
        st.Page(
            str(PAGES_DIR / "07_mercado_brasil.py"),
            title="Mercado Brasileiro",
            icon=":material/flag:",
            url_path="mercado-brasil",
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
            str(PAGES_DIR / "08_analises_comparativas.py"),
            title="Análises & Comparações",
            icon=":material/analytics:",
            url_path="analises-comparativas",
        ),
    ],
    "⚙️ Infraestrutura": [
        st.Page(
            str(PAGES_DIR / "09_observabilidade.py"),
            title="Observabilidade",
            icon=":material/monitoring:",
            url_path="observabilidade",
        ),
    ],
}

# Inicialização da navegação
pg = st.navigation(pages)

# Rodapé minimalista da barra lateral
with st.sidebar:
    st.divider()
    st.caption("FertiPartner • Inteligência de Mercado Agrícola")

# Execução da página selecionada
pg.run()

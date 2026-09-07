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
    initial_sidebar_state="collapsed",
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


CATALOG_DIR = PAGES_DIR / "catalogo_de_fertilizantes"

# Estrutura moderna de navegação organizada pelo Catálogo Central e Categorias Agronômicas em pastas dedicadas
pages = {
    "🌐 Visão Geral": [
        st.Page(
            str(PAGES_DIR / "01_inicio.py"),
            title="Início",
            icon=":material/home:",
            default=True,
            url_path="inicio",
        ),
    ],
    "📦 Catálogo de Fertilizantes": [
        st.Page(
            str(CATALOG_DIR / "catalogo.py"),
            title="Hub Central do Catálogo",
            icon=":material/menu_book:",
            url_path="catalogo",
        ),
    ],
    "🌱 Catálogo • Primários: Nitrogenados": [
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "ureia.py"), title="Ureia", icon=":material/science:", url_path="fert-ureia"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "amonia_anidra.py"), title="Amônia Anidra", icon=":material/science:", url_path="fert-amonia-anidra"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "nitrato_de_amonio.py"), title="Nitrato de Amônio", icon=":material/science:", url_path="fert-nitrato-de-amonio"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "sulfato_de_amonio.py"), title="Sulfato de Amônio", icon=":material/science:", url_path="fert-sulfato-de-amonio"),
    ],
    "🌱 Catálogo • Primários: Fosfatados": [
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "map.py"), title="Fosfato Monoamônico (MAP)", icon=":material/science:", url_path="fert-map"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "dap.py"), title="Fosfato Diamônico (DAP)", icon=":material/science:", url_path="fert-dap"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "ssp.py"), title="Superfosfato Simples (SSP)", icon=":material/science:", url_path="fert-ssp"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "tsp.py"), title="Superfosfato Triplo (TSP)", icon=":material/science:", url_path="fert-tsp"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "rocha_fosfatica.py"), title="Rocha Fosfática", icon=":material/science:", url_path="fert-rocha-fosfatica"),
    ],
    "🌱 Catálogo • Primários: Potássicos": [
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "potassicos" / "cloreto_de_potassio.py"), title="Cloreto de Potássio (KCl)", icon=":material/science:", url_path="fert-cloreto-de-potassio"),
        st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "potassicos" / "sulfato_de_potassio.py"), title="Sulfato de Potássio (SOP)", icon=":material/science:", url_path="fert-sulfato-de-potassio"),
    ],
    "🌿 Catálogo • Macronutrientes Secundários": [
        st.Page(str(CATALOG_DIR / "macronutrientes_secundarios" / "enxofre_elementar.py"), title="Enxofre Elementar", icon=":material/science:", url_path="fert-enxofre-elementar"),
    ],
    "🔬 Catálogo • Micronutrientes": [
        st.Page(str(CATALOG_DIR / "micronutrientes" / "micronutrientes.py"), title="Micronutrientes (Geral)", icon=":material/biotech:", url_path="fert-micronutrientes"),
    ],
    "💡 Inteligência": [
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

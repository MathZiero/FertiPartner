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


PAGES_DIR = _find_pages_dir()
CATALOG_DIR = PAGES_DIR / "catalogo_de_fertilizantes"

# Definição de todas as páginas da aplicação
p_inicio = st.Page(
    str(PAGES_DIR / "01_inicio.py"),
    title="Início",
    icon=":material/home:",
    default=True,
    url_path="inicio",
)

# Primários: Nitrogenados
p_ureia = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "ureia.py"), title="Ureia", icon=":material/science:", url_path="fert-ureia")
p_amonia = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "amonia_anidra.py"), title="Amônia Anidra", icon=":material/science:", url_path="fert-amonia-anidra")
p_nitrato = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "nitrato_de_amonio.py"), title="Nitrato de Amônio", icon=":material/science:", url_path="fert-nitrato-de-amonio")
p_sulfato_amonio = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "nitrogenados" / "sulfato_de_amonio.py"), title="Sulfato de Amônio", icon=":material/science:", url_path="fert-sulfato-de-amonio")

# Primários: Fosfatados
p_map = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "map.py"), title="Fosfato Monoamônico (MAP)", icon=":material/science:", url_path="fert-map")
p_dap = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "dap.py"), title="Fosfato Diamônico (DAP)", icon=":material/science:", url_path="fert-dap")
p_ssp = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "ssp.py"), title="Superfosfato Simples (SSP)", icon=":material/science:", url_path="fert-ssp")
p_tsp = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "tsp.py"), title="Superfosfato Triplo (TSP)", icon=":material/science:", url_path="fert-tsp")
p_rocha = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "fosfatados" / "rocha_fosfatica.py"), title="Rocha Fosfática", icon=":material/science:", url_path="fert-rocha-fosfatica")

# Primários: Potássicos
p_kcl = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "potassicos" / "cloreto_de_potassio.py"), title="Cloreto de Potássio (KCl)", icon=":material/science:", url_path="fert-cloreto-de-potassio")
p_sop = st.Page(str(CATALOG_DIR / "macronutrientes_primarios" / "potassicos" / "sulfato_de_potassio.py"), title="Sulfato de Potássio (SOP)", icon=":material/science:", url_path="fert-sulfato-de-potassio")

# Macronutrientes Secundários
p_enxofre = st.Page(str(CATALOG_DIR / "macronutrientes_secundarios" / "enxofre_elementar.py"), title="Enxofre Elementar", icon=":material/science:", url_path="fert-enxofre-elementar")

# Micronutrientes
p_micronutrientes = st.Page(str(CATALOG_DIR / "micronutrientes" / "micronutrientes.py"), title="Micronutrientes (Geral)", icon=":material/biotech:", url_path="fert-micronutrientes")

# Inteligência & Infraestrutura
p_analises = st.Page(
    str(PAGES_DIR / "08_analises_comparativas.py"),
    title="Análises & Comparações",
    icon=":material/analytics:",
    url_path="analises-comparativas",
)
p_noticias = st.Page(
    str(PAGES_DIR / "10_noticias_mercado.py"),
    title="Radar de Notícias NPK",
    icon=":material/newspaper:",
    url_path="noticias-mercado",
)
p_ai = st.Page(
    str(PAGES_DIR / "11_assistente_ia.py"),
    title="FertiPartner.AI",
    icon=":material/smart_toy:",
    url_path="fertipartner-ai",
)
p_observabilidade = st.Page(
    str(PAGES_DIR / "09_observabilidade.py"),
    title="Observabilidade",
    icon=":material/monitoring:",
    url_path="observabilidade",
)

# Agrupamento estruturado por tipo de nutriente
nitrogenados_pages = [p_ureia, p_amonia, p_nitrato, p_sulfato_amonio]
fosfatados_pages = [p_map, p_dap, p_ssp, p_tsp, p_rocha]
potassicos_pages = [p_kcl, p_sop]
secundarios_pages = [p_enxofre]
micronutrientes_pages = [p_micronutrientes]

# Mapeamento completo para registro de rotas no Streamlit
pages = {
    "🌐 Visão Geral": [p_inicio],
    "📦 Catálogo de Fertilizantes": [
        *nitrogenados_pages,
        *fosfatados_pages,
        *potassicos_pages,
        *secundarios_pages,
        *micronutrientes_pages,
    ],
    "💡 Inteligência": [p_analises, p_noticias, p_ai],
    "⚙️ Infraestrutura": [p_observabilidade],
}

# Inicialização da navegação oculta para controle total da hierarquia com submenus na barra lateral
pg = st.navigation(pages, position="hidden")

# Identifica qual grupo nutricional está ativo para manter o submenu correspondente aberto
is_nitrogenados = pg in nitrogenados_pages
is_fosfatados = pg in fosfatados_pages
is_potassicos = pg in potassicos_pages
is_secundarios = pg in secundarios_pages
is_micronutrientes = pg in micronutrientes_pages

# Renderização do menu estruturado com submenus na barra lateral
with st.sidebar:
    # 🌐 Visão Geral
    st.page_link(p_inicio, label="Início", icon=":material/home:", width="stretch")

    st.divider()

    # 📦 Catálogo de Fertilizantes - Submenus por Tipo de Nutriente
    st.markdown(
        "<div style='font-size: 0.76rem; font-weight: 700; color: #52796F; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.45rem;'>"
        "📦 Catálogo de Fertilizantes"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("🌱 Primários: Nitrogenados", expanded=is_nitrogenados):
        st.page_link(p_ureia, label="Ureia", icon=":material/science:", width="stretch")
        st.page_link(p_amonia, label="Amônia Anidra", icon=":material/science:", width="stretch")
        st.page_link(p_nitrato, label="Nitrato de Amônio", icon=":material/science:", width="stretch")
        st.page_link(p_sulfato_amonio, label="Sulfato de Amônio", icon=":material/science:", width="stretch")

    with st.expander("🌾 Primários: Fosfatados", expanded=is_fosfatados):
        st.page_link(p_map, label="Fosfato Monoamônico (MAP)", icon=":material/science:", width="stretch")
        st.page_link(p_dap, label="Fosfato Diamônico (DAP)", icon=":material/science:", width="stretch")
        st.page_link(p_ssp, label="Superfosfato Simples (SSP)", icon=":material/science:", width="stretch")
        st.page_link(p_tsp, label="Superfosfato Triplo (TSP)", icon=":material/science:", width="stretch")
        st.page_link(p_rocha, label="Rocha Fosfática", icon=":material/science:", width="stretch")

    with st.expander("🌿 Primários: Potássicos", expanded=is_potassicos):
        st.page_link(p_kcl, label="Cloreto de Potássio (KCl)", icon=":material/science:", width="stretch")
        st.page_link(p_sop, label="Sulfato de Potássio (SOP)", icon=":material/science:", width="stretch")

    with st.expander("🍃 Secundários", expanded=is_secundarios):
        st.page_link(p_enxofre, label="Enxofre Elementar", icon=":material/science:", width="stretch")

    with st.expander("🔬 Micronutrientes", expanded=is_micronutrientes):
        st.page_link(p_micronutrientes, label="Micronutrientes (Geral)", icon=":material/biotech:", width="stretch")

    st.divider()

    # 💡 Inteligência
    st.markdown(
        "<div style='font-size: 0.76rem; font-weight: 700; color: #52796F; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.45rem;'>"
        "💡 Inteligência"
        "</div>",
        unsafe_allow_html=True,
    )
    st.page_link(p_analises, label="Análises & Comparações", icon=":material/analytics:", width="stretch")
    st.page_link(p_noticias, label="Radar de Notícias NPK", icon=":material/newspaper:", width="stretch")
    st.page_link(p_ai, label="FertiPartner.AI", icon=":material/smart_toy:", width="stretch")

    # ⚙️ Infraestrutura
    st.markdown(
        "<div style='font-size: 0.76rem; font-weight: 700; color: #52796F; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.45rem; margin-top: 0.6rem;'>"
        "⚙️ Infraestrutura"
        "</div>",
        unsafe_allow_html=True,
    )
    st.page_link(p_observabilidade, label="Observabilidade", icon=":material/monitoring:", width="stretch")

    st.divider()
    st.caption("FertiPartner • Inteligência de Mercado Agrícola")

# Execução da página selecionada
pg.run()


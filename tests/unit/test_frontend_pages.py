"""Testes unitários para validar a estrutura e conformidade das páginas do Streamlit."""

from pathlib import Path
import py_compile
import importlib.util
import pytest

from app.presentation.streamlit.components import ui

PAGES_DIR = Path(__file__).resolve().parents[2] / "src" / "app" / "presentation" / "streamlit" / "pages"

PAGE_FILES = [
    "01_inicio.py",
    "01_visao_geral.py",
    "03_producao_global.py",
    "04_comercio_internacional.py",
    "05_fluxos_sankey.py",
    "06_precos_benchmarks.py",
    "07_mercado_brasil.py",
    "08_analises_comparativas.py",
    "09_observabilidade.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/nitrogenados/ureia.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/nitrogenados/amonia_anidra.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/nitrogenados/nitrato_de_amonio.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/nitrogenados/sulfato_de_amonio.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/fosfatados/map.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/fosfatados/dap.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/fosfatados/ssp.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/fosfatados/tsp.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/fosfatados/rocha_fosfatica.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/potassicos/cloreto_de_potassio.py",
    "catalogo_de_fertilizantes/macronutrientes_primarios/potassicos/sulfato_de_potassio.py",
    "catalogo_de_fertilizantes/macronutrientes_secundarios/enxofre_elementar.py",
    "catalogo_de_fertilizantes/micronutrientes/micronutrientes.py",
]


def test_all_page_files_exist():
    """Garante que todos os arquivos das páginas Streamlit existem no diretório pages/."""
    assert PAGES_DIR.exists(), f"Diretório {PAGES_DIR} não encontrado"
    for page_name in PAGE_FILES:
        page_path = PAGES_DIR / page_name
        assert page_path.exists(), f"Página {page_name} não encontrada em {PAGES_DIR}"


@pytest.mark.parametrize("page_name", PAGE_FILES)
def test_page_files_compile(page_name):
    """Garante que cada arquivo de página compila perfeitamente sem erros de sintaxe."""
    page_path = PAGES_DIR / page_name
    assert page_path.exists()
    compiled = py_compile.compile(str(page_path), doraise=True)
    assert compiled is not None


@pytest.mark.parametrize("page_name", PAGE_FILES)
def test_page_defines_render_page_callable(page_name):
    """Garante que cada página define a função render_page() chamável sem executar no import."""
    page_path = PAGES_DIR / page_name
    spec = importlib.util.spec_from_file_location(f"test_mod_{page_name.replace('.', '_')}", page_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Ao carregar o módulo em ambiente isolado, como __name__ != '__main__', não deve renderizar nada
    spec.loader.exec_module(module)
    assert hasattr(module, "render_page"), f"{page_name} não possui a função render_page"
    assert callable(module.render_page), f"{page_name}.render_page não é chamável"


def test_ui_components_exist_and_callable():
    """Valida a existência dos componentes nativos em components/ui.py."""
    expected_funcs = [
        "render_header",
        "render_kpi_card",
        "render_source_badge",
        "render_download_csv_button",
        "show_fertilizer_details_modal",
        "render_units_legend",
    ]
    for func_name in expected_funcs:
        assert hasattr(ui, func_name), f"ui.{func_name} não encontrado"
        assert callable(getattr(ui, func_name)), f"ui.{func_name} não é chamável"


def test_root_main_exists_and_compiles():
    """Garante que o ponto de entrada main.py na raiz do projeto existe e compila."""
    root_main = Path(__file__).resolve().parents[2] / "main.py"
    assert root_main.exists(), "Arquivo main.py na raiz não encontrado"
    compiled = py_compile.compile(str(root_main), doraise=True)
    assert compiled is not None


def test_dashboard_compiles_and_contains_updated_categories():
    """Garante que o dashboard.py compila e define as novas categorias agronômicas de navegação."""
    dashboard_path = Path(__file__).resolve().parents[2] / "src" / "app" / "presentation" / "streamlit" / "dashboard.py"
    assert dashboard_path.exists(), "dashboard.py não encontrado"
    compiled = py_compile.compile(str(dashboard_path), doraise=True)
    assert compiled is not None

    content = dashboard_path.read_text(encoding="utf-8")
    assert 'initial_sidebar_state="collapsed"' in content, "Sidebar deve ser colapsada por padrão"
    assert "Catálogo de Fertilizantes" in content, "Catálogo não encontrado no dashboard"
    assert "Primários: Nitrogenados" in content, "Subdivisão 'Primários: Nitrogenados' não encontrada no dashboard"
    assert "Primários: Fosfatados" in content, "Subdivisão 'Primários: Fosfatados' não encontrada no dashboard"
    assert "Primários: Potássicos" in content, "Subdivisão 'Primários: Potássicos' não encontrada no dashboard"
    assert "Secundários" in content, "Categoria 'Secundários' não encontrada no dashboard"
    assert "Micronutrientes" in content, "Categoria 'Micronutrientes' não encontrada no dashboard"
    assert "💡 Inteligência" in content, "Categoria '💡 Inteligência' não encontrada no dashboard"
    assert "catalogo_de_fertilizantes" in content, "Pasta catalogo_de_fertilizantes não referenciada no dashboard"
    assert "macronutrientes_primarios" in content, "Pasta macronutrientes_primarios não referenciada no dashboard"
    assert "nitrogenados" in content, "Subpasta nitrogenados não referenciada no dashboard"
    assert "fosfatados" in content, "Subpasta fosfatados não referenciada no dashboard"
    assert "potassicos" in content, "Subpasta potassicos não referenciada no dashboard"
    assert "macronutrientes_secundarios" in content, "Pasta macronutrientes_secundarios não referenciada no dashboard"
    assert "ureia.py" in content, "Página da Ureia não encontrada no dashboard"
    assert "map.py" in content, "Página do MAP não encontrada no dashboard"
    assert "cloreto_de_potassio.py" in content, "Página do KCl não encontrada no dashboard"
    assert "enxofre_elementar.py" in content, "Página do Enxofre não encontrada no dashboard"
    assert "micronutrientes.py" in content, "Página de Micronutrientes não encontrada no dashboard"
    assert "catalogo.py" not in content, "catalogo.py (Hub Central) não deve ser referenciado no dashboard"
    assert "02_catalogo.py" not in content, "02_catalogo.py não deve ser referenciado no dashboard"
    assert "Catálogo •" not in content, "Não devem existir categorias 'Catálogo • ...' divididas no dashboard"
    assert 'position="hidden"' in content, "st.navigation deve usar position='hidden' para controle de submenus"
    assert "st.expander" in content, "Submenus por tipo de nutriente devem usar st.expander"
    assert "st.page_link" in content, "Páginas devem ser acessíveis via st.page_link na barra lateral"


def test_catalogo_folder_hierarchy_exists():
    """Valida que a pasta 'catalogo_de_fertilizantes' possui as subpastas corretas."""
    cat_dir = PAGES_DIR / "catalogo_de_fertilizantes"
    assert cat_dir.is_dir(), "Pasta catalogo_de_fertilizantes não existe"

    prim_dir = cat_dir / "macronutrientes_primarios"
    sec_dir = cat_dir / "macronutrientes_secundarios"
    micro_dir = cat_dir / "micronutrientes"
    assert prim_dir.is_dir(), "Pasta macronutrientes_primarios não existe"
    assert sec_dir.is_dir(), "Pasta macronutrientes_secundarios não existe"
    assert micro_dir.is_dir(), "Pasta micronutrientes não existe"

    nit_dir = prim_dir / "nitrogenados"
    fos_dir = prim_dir / "fosfatados"
    pot_dir = prim_dir / "potassicos"
    assert nit_dir.is_dir(), "Pasta nitrogenados não existe"
    assert fos_dir.is_dir(), "Pasta fosfatados não existe"
    assert pot_dir.is_dir(), "Pasta potassicos não existe"



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
    "02_catalogo.py",
    "03_producao_global.py",
    "04_comercio_internacional.py",
    "05_fluxos_sankey.py",
    "06_precos_benchmarks.py",
    "07_mercado_brasil.py",
    "08_analises_comparativas.py",
    "09_observabilidade.py",
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
    """Garante que o dashboard.py compila e define as novas categorias de navegação."""
    dashboard_path = Path(__file__).resolve().parents[2] / "src" / "app" / "presentation" / "streamlit" / "dashboard.py"
    assert dashboard_path.exists(), "dashboard.py não encontrado"
    compiled = py_compile.compile(str(dashboard_path), doraise=True)
    assert compiled is not None

    content = dashboard_path.read_text(encoding="utf-8")
    assert "⚖️ Oferta e Demanda" in content, "Categoria '⚖️ Oferta e Demanda' não encontrada no dashboard"
    assert "📈 Preços" in content, "Categoria '📈 Preços' não encontrada no dashboard"
    assert "💡 Inteligência" in content, "Categoria '💡 Inteligência' não encontrada no dashboard"
    assert "03_producao_global.py" in content, "Página de Produção Global não encontrada no dashboard"


"""Catálogo Central de Fertilizantes."""

from app.presentation.streamlit.views.v02_fertilizers_catalog import render_view


def render_page() -> None:
    """Renderiza a página principal do Catálogo de Fertilizantes."""
    render_view()


if __name__ == "__main__":
    render_page()

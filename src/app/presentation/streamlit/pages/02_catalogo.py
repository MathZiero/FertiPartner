"""Página 2: Catálogo Físico-Químico e Agronômico de Fertilizantes."""

from app.presentation.streamlit.views.v02_fertilizers_catalog import render_view


def render_page() -> None:
    """Renderiza a página de catálogo delegando para a view v02."""
    render_view()


if __name__ == "__main__":
    render_page()

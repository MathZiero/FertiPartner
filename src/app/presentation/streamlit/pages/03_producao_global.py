"""Página 3: Produção Global e Ranking Mundial de Produtores."""

from app.presentation.streamlit.views.v03_global_production import render_view


def render_page() -> None:
    """Renderiza a página de produção global delegando para a view v03."""
    render_view()


if __name__ == "__main__":
    render_page()

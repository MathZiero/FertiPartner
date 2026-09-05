"""Página 8: Análise Comparativa e Correlações Multidimensionais."""

from app.presentation.streamlit.views.v08_comparative_analytics import render_view


def render_page() -> None:
    """Renderiza a página de análises comparativas delegando para a view v08."""
    render_view()


if __name__ == "__main__":
    render_page()

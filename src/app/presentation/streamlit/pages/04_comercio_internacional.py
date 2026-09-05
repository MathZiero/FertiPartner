"""Página 4: Comércio Internacional e Fluxos de Exportação/Importação."""

from app.presentation.streamlit.views.v04_international_trade import render_view


def render_page() -> None:
    """Renderiza a página de comércio internacional delegando para a view v04."""
    render_view()


if __name__ == "__main__":
    render_page()

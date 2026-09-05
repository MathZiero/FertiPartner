"""Página 1: Início - Ponto de partida da plataforma FertiPartner."""

from app.presentation.streamlit.views.v01_inicio import render_view


def render_page() -> None:
    """Renderiza a página Início delegando para a view v01."""
    render_view()


if __name__ == "__main__":
    render_page()

"""Página de Software: Arquitetura, Engenharia de Software e Modelagem de Dados."""

from app.presentation.streamlit.views.v12_software_architecture import render_view


def render_page() -> None:
    """Renderiza a página de Arquitetura de Software delegando para a view v12."""
    render_view()


if __name__ == "__main__":
    render_page()

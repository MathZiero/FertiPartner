"""Página de Observabilidade: Status das fontes, monitoramento de coletas e integridade operacional."""

from app.presentation.streamlit.views.v09_system_health import render_view


def render_page() -> None:
    """Renderiza a página de observabilidade delegando para a view v09."""
    render_view()


if __name__ == "__main__":
    render_page()

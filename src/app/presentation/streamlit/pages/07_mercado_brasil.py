"""Página 7: Mercado Brasileiro, Consumo Aparente e Dependência Estratégica."""

from app.presentation.streamlit.views.v07_brazil_market import render_view


def render_page() -> None:
    """Renderiza a página de mercado brasileiro delegando para a view v07."""
    render_view()


if __name__ == "__main__":
    render_page()

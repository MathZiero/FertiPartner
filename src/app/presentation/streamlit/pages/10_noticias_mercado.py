"""Página 10: Radar de Notícias e Fatos Relevantes de Fertilizantes (Google News)."""

from app.presentation.streamlit.views.v10_market_news import render_view


def render_page() -> None:
    """Renderiza a página de notícias e tendências de mercado."""
    render_view()


if __name__ == "__main__":
    render_page()

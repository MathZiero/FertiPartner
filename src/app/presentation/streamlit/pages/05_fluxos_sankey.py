"""Página 5: Fluxos Comerciais Bilaterais com Diagrama Sankey Interativo."""

from app.presentation.streamlit.views.v05_trade_flows_sankey import render_view


def render_page() -> None:
    """Renderiza a página de fluxos comerciais delegando para a view v05."""
    render_view()


if __name__ == "__main__":
    render_page()

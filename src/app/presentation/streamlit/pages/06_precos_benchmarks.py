"""Página 6: Preços Internacionais e Benchmarks de Mercado."""

from app.presentation.streamlit.views.v06_price_benchmarks import render_view


def render_page() -> None:
    """Renderiza a página de preços e benchmarks delegando para a view v06."""
    render_view()


if __name__ == "__main__":
    render_page()

"""Página dedicada do fertilizante: Superfosfato Simples (SSP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Superfosfato Simples (SSP)."""
    render_fertilizer_page("ssp")


if __name__ == "__main__":
    render_page()

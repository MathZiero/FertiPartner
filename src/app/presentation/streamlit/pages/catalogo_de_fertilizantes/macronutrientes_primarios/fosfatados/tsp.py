"""Página dedicada do fertilizante: Superfosfato Triplo (TSP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do TSP."""
    render_fertilizer_page("tsp")


if __name__ == "__main__":
    render_page()

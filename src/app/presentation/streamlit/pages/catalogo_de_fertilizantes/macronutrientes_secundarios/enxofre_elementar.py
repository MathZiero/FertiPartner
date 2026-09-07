"""Página dedicada do fertilizante: Enxofre Elementar Pastilhado."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Enxofre Elementar."""
    render_fertilizer_page("enxofre-elementar")


if __name__ == "__main__":
    render_page()

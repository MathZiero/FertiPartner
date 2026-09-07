"""Página dedicada do fertilizante: Amônia Anidra."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado da Amônia Anidra."""
    render_fertilizer_page("amonia-anidra")


if __name__ == "__main__":
    render_page()

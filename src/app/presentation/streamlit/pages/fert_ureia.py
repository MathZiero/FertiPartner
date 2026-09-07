"""Página dedicada do fertilizante: Ureia."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado da Ureia."""
    render_fertilizer_page("ureia")


if __name__ == "__main__":
    render_page()

"""Página dedicada do fertilizante: Sulfato de Amônio."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Sulfato de Amônio."""
    render_fertilizer_page("sulfato-de-amonio")


if __name__ == "__main__":
    render_page()

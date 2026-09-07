"""Página dedicada do fertilizante: Nitrato de Amônio."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Nitrato de Amônio."""
    render_fertilizer_page("nitrato-de-amonio")


if __name__ == "__main__":
    render_page()

"""Página dedicada do fertilizante: Sulfato de Potássio (SOP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Sulfato de Potássio (SOP)."""
    render_fertilizer_page("sulfato-de-potassio")


if __name__ == "__main__":
    render_page()

"""Página dedicada: Panorama de Micronutrientes na Agricultura."""

from app.presentation.streamlit.views.v_micronutrients import render_page as _render_micro


def render_page() -> None:
    """Renderiza a página de Micronutrientes."""
    _render_micro()


if __name__ == "__main__":
    render_page()

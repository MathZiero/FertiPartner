"""Página analítica de mercado dos Micronutrientes."""

from app.presentation.streamlit.views.v_micronutrients import render_micronutrients_page


def render_page() -> None:
    """Renderiza o painel analítico dos Micronutrientes."""
    render_micronutrients_page()


if __name__ == "__main__":
    render_page()

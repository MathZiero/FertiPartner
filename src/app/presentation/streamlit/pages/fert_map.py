"""Página dedicada do fertilizante: Fosfato Monoamônico (MAP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Fosfato Monoamônico (MAP)."""
    render_fertilizer_page("map")


if __name__ == "__main__":
    render_page()

"""Página dedicada do fertilizante: Fosfato Diamônico (DAP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Fosfato Diamônico (DAP)."""
    render_fertilizer_page("dap")


if __name__ == "__main__":
    render_page()

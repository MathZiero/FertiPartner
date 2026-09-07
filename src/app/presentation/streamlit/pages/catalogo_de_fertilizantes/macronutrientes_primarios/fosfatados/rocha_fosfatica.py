"""Página dedicada do fertilizante: Rocha Fosfática Concentrada."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado da Rocha Fosfática."""
    render_fertilizer_page("rocha-fosfatica")


if __name__ == "__main__":
    render_page()

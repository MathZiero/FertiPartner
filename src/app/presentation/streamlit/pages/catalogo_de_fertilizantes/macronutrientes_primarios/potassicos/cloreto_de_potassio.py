"""Página dedicada do fertilizante: Cloreto de Potássio (KCl / MOP)."""

from app.presentation.streamlit.views.v_fertilizer_detail import render_fertilizer_page


def render_page() -> None:
    """Renderiza o painel dedicado do Cloreto de Potássio."""
    render_fertilizer_page("cloreto-de-potassio")


if __name__ == "__main__":
    render_page()

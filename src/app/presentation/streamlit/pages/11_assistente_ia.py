"""Página do FertiPartner.AI - Assistente Especialista em Fertilizantes."""

from app.presentation.streamlit.views.v11_fertipartner_ai import render_view


def render_page() -> None:
    """Renderiza a página do FertiPartner.AI."""
    render_view()


if __name__ == "__main__":
    render_page()

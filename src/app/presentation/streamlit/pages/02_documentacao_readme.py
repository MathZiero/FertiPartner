"""Página de Documentação: Renderiza o README.md oficial da codebase."""

from app.presentation.streamlit.views.v02_documentacao_readme import render_view


def render_page() -> None:
    """Renderiza a documentação README delegando para a view v02_documentacao_readme."""
    render_view()


if __name__ == "__main__":
    render_page()

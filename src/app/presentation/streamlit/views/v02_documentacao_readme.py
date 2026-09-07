"""View para visualização da documentação oficial (README.md) da codebase."""

from pathlib import Path
import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
)

ROOT_DIR = Path(__file__).resolve().parents[5]
README_PATH = ROOT_DIR / "README.md"


def render_view() -> None:
    """Renderiza o arquivo README.md da codebase diretamente no Streamlit."""
    render_header(
        title="Documentação do Projeto (README)",
        subtitle="Especificações de engenharia, arquitetura de dados 4NF, agentes de IA com GuardRails e guia de execução da plataforma FertiPartner.",
        badge_text="Codebase Docs",
        badge_type="emerald",
    )

    if not README_PATH.exists():
        st.error(f"Arquivo README.md não localizado no caminho: {README_PATH}")
        return

    readme_content = README_PATH.read_text(encoding="utf-8")

    c_dl, _ = st.columns([3, 9])
    with c_dl:
        st.download_button(
            label="Baixar README.md",
            data=readme_content,
            file_name="README.md",
            mime="text/markdown",
            icon=":material/download:",
            width="stretch",
        )

    st.write("")

    with st.container(border=True):
        st.markdown(readme_content, unsafe_allow_html=True)

    st.divider()
    render_source_badge("Repositório Oficial FertiPartner • GitHub", "Markdown Nativo")


if __name__ == "__main__":
    render_view()

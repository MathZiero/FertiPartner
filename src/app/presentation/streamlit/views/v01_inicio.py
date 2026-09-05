"""Página Inicial (Início): Ponto de partida da plataforma FertiPartner."""

import streamlit as st

from app.presentation.streamlit.components.ui import render_header


def render_view() -> None:
    render_header(
        title="FertiPartner — Inteligência do Mercado de Fertilizantes",
        subtitle="Plataforma analítica e estratégica para monitoramento de produção mundial, comércio exterior, cotações de preços e dependência do mercado brasileiro.",
        badge_text="Início",
        badge_type="emerald",
    )

    st.divider()

    st.markdown(
        """
        ### Bem-vindo ao FertiPartner
        
        Utilize a barra de navegação lateral para explorar os módulos da plataforma:
        
        - 🌐 **Visão Geral**: Acesse a página inicial ou consulte o **Catálogo de Fertilizantes** com especificações e fichas técnicas.
        - 🏭 **Produção**: Visualize o mapeamento da **Produção Global** e o ranking mundial de síntese e mineração via FAOSTAT.
        - 🚢 **Comércio**: Explore as trocas no **Comércio Internacional**, os corredores logísticos no diagrama **Fluxos Sankey** e o balanço do **Mercado Brasileiro**.
        - 📈 **Preços & Inteligência**: Acompanhe as cotações de mercado em **Preços & Benchmarks** e realize **Análises Comparativas**.
        - ⚙️ **Infraestrutura**: Monitore os pipelines de ingestão e a consistência do banco de dados em **Observabilidade**.
        """
    )

    st.divider()


def render_page() -> None:
    render_view()


if __name__ == "__main__":
    render_page()

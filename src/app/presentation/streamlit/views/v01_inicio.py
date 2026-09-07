"""Página Inicial (Início): Ponto de partida da plataforma FertiPartner."""

import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
)


def render_view() -> None:
    """Renderiza a página inicial explicando o propósito do FertiPartner sob óticas de negócio e software."""
    render_header(
        title="FertiPartner — Inteligência do Mercado de Fertilizantes",
        subtitle="Plataforma estratégica de inteligência de dados, cotações internacionais, balanço de suprimentos e suporte à decisão na cadeia de nutrição vegetal.",
        badge_text="Visão Executiva",
        badge_type="emerald",
    )

    st.markdown(
        """
        ### O que é o FertiPartner?
        
        O **FertiPartner** é uma plataforma analítica desenvolvida para transformar dados complexos e dispersos do mercado
        global e doméstico de fertilizantes em inteligência acionável para o agronegócio. 
        
        A plataforma centraliza informações sobre **Macronutrientes Primários (Nitrogênio, Fósforo e Potássio — NPK)**, 
        **Macronutrientes Secundários (Enxofre)** e **Micronutrientes**, conectando fluxos de comércio exterior, capacidade 
        produtiva mundial, cotações de referência internacional e dinâmicas de distribuição regional no Brasil.
        """
    )

    st.write("")

    # Colunas de Perspectivas: Negócio vs Solução de Software
    col_biz, col_tech = st.columns(2)

    with col_biz:
        st.markdown(
            """
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #2D6A4F;
                border-radius: 12px;
                padding: 1.5rem;
                height: 100%;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
            ">
                <div style="font-weight: 800; color: #1B4332; font-size: 1.15rem; margin-bottom: 0.75rem;">
                    Para que Serve: Perspectiva de Negócio & Agronegócio
                </div>
                <div style="font-size: 0.88rem; color: #374151; line-height: 1.6;">
                    O Brasil é o quarto maior consumidor global de fertilizantes e importa cerca de <b>85%</b> de sua demanda anual,
                    enfrentando vulnerabilidade estrutural a choques geopolíticos, oscilações cambiais e gargalos portuários.
                    <br><br>
                    <b>Impactos Diretos para Tomada de Decisão:</b>
                    <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                        <li><b>Mitigação de Risco de Suprimento:</b> Monitoramento antecipado de volumes aduaneiros e capacidade produtiva dos grandes polos mundiais (Rússia, Canadá, China, Marrocos).</li>
                        <li><b>Janelas Oportunas de Aquisição (Barter):</b> Acompanhamento da paridade de troca histórica entre fertilizantes (ex.: Ureia, MAP, KCl) e sacas de commodities agrícolas (soja e milho).</li>
                        <li><b>Planejamento de Safra e Safrinha:</b> Avaliação de estoques de passagem, fluxos de internalização por porto (Paranaguá, Santos, Itaqui) e demanda por Unidade Federativa.</li>
                        <li><b>Conhecimento Técnico e Agronômico:</b> Catálogo completo com teores de garantia nutricional, umidade crítica relativa (PCUR) e compatibilidade química de misturas.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_tech:
        st.markdown(
            """
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #52796F;
                border-radius: 12px;
                padding: 1.5rem;
                height: 100%;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
            ">
                <div style="font-weight: 800; color: #1B4332; font-size: 1.15rem; margin-bottom: 0.75rem;">
                    Para que Serve: Perspectiva de Engenharia & Software
                </div>
                <div style="font-size: 0.88rem; color: #374151; line-height: 1.6;">
                    Como solução de engenharia de software, o FertiPartner resolve o desafio da dispersão e heterogeneidade
                    de formatos públicos em pipelines auditáveis, escaláveis e de alta confiabilidade.
                    <br><br>
                    <b>Pilares da Solução Tecnológica:</b>
                    <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                        <li><b>Modelagem em Quarta Forma Normal (4NF):</b> Persistência relacional em PostgreSQL/Supabase que elimina anomalias de atualização e desagrega fatos temporais atômicos.</li>
                        <li><b>Clean Architecture & DDD:</b> Isolamento absoluto de regras de negócio de bibliotecas externas, frameworks de UI ou mecanismos de banco de dados.</li>
                        <li><b>FertiPartner.AI com GuardRails:</b> Motor de IA baseado em Google Gemini 3.x Flash com Function Calling determinístico em dados tabulares, Thought Signature e blindagem contra Prompt Injection.</li>
                        <li><b>Resiliência Operacional & TDD:</b> Pipelines com backoff exponencial, jitter, auditoria criptográfica por hash SHA-256 e mais de 165 testes unitários automatizados.</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.divider()

    # Módulos de Navegação
    st.markdown("### Estrutura e Módulos da Plataforma")
    st.markdown(
        """
        Navegue pelos menus laterais da aplicação para explorar as diferentes camadas de inteligência:
        
        - **Visão Geral**:
          - **Início**: Apresentação executiva da plataforma e proposta de valor.
          - **Documentação (README)**: Especificações técnicas, manual de execução e guia de implantação da codebase.
          
        - **Catálogo de Fertilizantes**:
          - **Primários: Nitrogenados**: Painéis individuais para Ureia, Amônia Anidra, Nitrato de Amônio e Sulfato de Amônio.
          - **Primários: Fosfatados**: Painéis individuais para MAP, DAP, SSP, TSP e Rocha Fosfática.
          - **Primários: Potássicos**: Painéis individuais para Cloreto de Potássio (KCl) e Sulfato de Potássio (SOP).
          - **Secundários**: Painel dedicado para Enxofre Elementar.
          - **Micronutrientes**: Panorama analítico de Zinco, Boro, Cobre, Manganês, Molibdênio e Cobalto.
          
        - **Inteligência**:
          - **Análises & Comparações**: Comparador de preços, paridades de troca, grau de vulnerabilidade externa, risco HHI e matriz de correlação.
          - **Radar de Notícias NPK**: Monitoramento em tempo real dos últimos 7 dias via Google News RSS com barômetros de sentimento setorial.
          - **FertiPartner.AI**: Assistente especialista cognitivo acoplado ao banco relacional via Function Calling com segurança por GuardRails.
          
        - **Infraestrutura**:
          - **Observabilidade**: Auditoria operacional de ingestão, fontes ativas, matriz de consistência e SLAs de dados.
          - **Software**: Especificações de engenharia de software, modelagem 4NF, Clean Architecture e arquitetura de IA.
        """
    )

    st.divider()
    render_source_badge("FertiPartner • Arquitetura & Inteligência de Mercado", "Versão Homologada")


def render_page() -> None:
    """Função invocada pelo Streamlit ao renderizar a página."""
    render_view()


if __name__ == "__main__":
    render_page()

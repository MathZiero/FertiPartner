"""Radar de Notícias e Fatos Relevantes de Fertilizantes (Google News RSS)."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
)
from app.presentation.streamlit.services.news_service import GoogleNewsService

def _create_gauge_indicator(score_val: float, classification: str) -> go.Figure:
    """Gera um barômetro semicircular compacto interativo via Plotly Indicator para análise de sentimento setorial."""
    if score_val >= 1.5:
        bar_color = "#10B981"  # Emerald / Melhorando
    elif score_val <= -1.5:
        bar_color = "#EF4444"  # Red / Piorando
    else:
        bar_color = "#3B82F6"  # Blue / Estável

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_val,
            number={
                "valueformat": "+.1f" if score_val > 0 else ".1f",
                "font": {"size": 17, "color": "#1B4332", "family": "Inter, sans-serif"},
                "suffix": " pts",
            },
            gauge={
                "axis": {
                    "range": [-10, 10],
                    "tickmode": "array",
                    "tickvals": [-10, -5, 0, 5, 10],
                    "ticktext": ["-10", "-5", "0", "+5", "+10"],
                    "tickfont": {"size": 7.5, "color": "#6B7280"},
                    "tickcolor": "#9CA3AF",
                },
                "bar": {"color": bar_color, "thickness": 0.24},
                "bgcolor": "#FFFFFF",
                "borderwidth": 1,
                "bordercolor": "#E5E7EB",
                "steps": [
                    {"range": [-10, -1.5], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [-1.5, 1.5], "color": "rgba(59, 130, 246, 0.12)"},
                    {"range": [1.5, 10], "color": "rgba(16, 185, 129, 0.18)"},
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 2.5},
                    "thickness": 0.8,
                    "value": score_val,
                },
            },
        )
    )

    fig.update_layout(
        height=125,
        margin=dict(l=8, r=8, t=8, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def render_view() -> None:
    render_header(
        title="Radar de Notícias - Mercado de Fertilizantes",
        subtitle="Monitoramento em tempo real de notícias setoriais dos últimos 7 dias: logística portuária, capacidade produtiva, ritmo de demanda das safras, paridade de preços e comércio internacional.",
        badge_text="Feed em Tempo Real",
        badge_type="emerald",
    )

    # Botão de atualização rápida do feed
    c_btn, c_note = st.columns([2.5, 5.5])
    with c_btn:
        if st.button("Recarregar Feed (Últimos 7 Dias)", width="stretch"):
            GoogleNewsService.fetch_fertilizer_news.clear()
            st.rerun()
    with c_note:
        st.caption("Filtro temporal estrito: apenas publicações das últimas 168 horas (7 dias) com impacto direto na cadeia de suprimentos e agronegócio.")

    # Busca de notícias com cache inteligente
    df_news = GoogleNewsService.fetch_fertilizer_news()

    if df_news.empty:
        st.warning("Nenhuma notícia dos últimos 7 dias foi encontrada no momento. Tente novamente mais tarde.")
        return

    # =========================================================================
    # BARÔMETROS DE ANÁLISE DE SENTIMENTO SETORIAL (PLOTLY)
    # =========================================================================
    st.markdown("#### Barômetros de Sentimento de Mercado (Últimos 7 Dias)")
    st.caption("Diagnóstico semântico automatizado por processamento léxico das notícias reais publicadas nas últimas 168 horas.")

    sentiments = GoogleNewsService.analyze_sentiment_by_topic(df_news)

    # Grid de 5 colunas com barômetros semicirculares em Plotly
    cols = st.columns(len(sentiments))
    for idx, sent in enumerate(sentiments):
        with cols[idx]:
            with st.container(border=True):
                # Título do tópico em HTML com suporte responsivo a quebra de linha sem cortes
                st.markdown(
                    f"""
                    <div style="
                        font-size: 0.80rem;
                        font-weight: 700;
                        color: #1B4332;
                        text-align: center;
                        text-transform: uppercase;
                        letter-spacing: 0.02em;
                        min-height: 2.3rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        line-height: 1.25;
                        margin-bottom: 0.15rem;
                    ">
                        {sent['short_name']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Barômetro real compacto com ponteiro e faixas coloridas
                fig_gauge = _create_gauge_indicator(
                    score_val=sent["score_val"],
                    classification=sent["classification"],
                )
                st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})

                # Badge de status e diagnóstico contextual
                st.markdown(
                    f"""
                    <div style="text-align: center; margin-top: -0.3rem; margin-bottom: 0.45rem;">
                        <span class="fp-badge fp-badge-{sent['badge_color']}" style="font-size: 0.70rem; padding: 0.18rem 0.6rem;">
                            {sent['classification']}
                        </span>
                    </div>
                    <div style="font-size: 0.75rem; color: #374151; font-weight: 600; line-height: 1.35; min-height: 2.1rem; text-align: center;">
                        {sent['status_label']}
                    </div>
                    <div style="font-size: 0.70rem; color: #6B7280; margin-top: 0.35rem; border-top: 1px dashed #E2E8F0; padding-top: 0.35rem; text-align: center;">
                        Volume: <b>{sent['news_count']}</b> matérias
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Nota explicativa da metodologia NLP
    with st.expander("Metodologia da Análise de Sentimento"):
        st.markdown(
            """
            **Como funciona o algoritmo de análise de sentimento:**
            1. **Processamento em Tempo Real:** O algoritmo extrai os textos integrais (títulos e resumos) das matérias captadas no feed RSS dos últimos 7 dias.
            2. **Segmentação Temática:** Cada notícia é mapeada para os 5 eixos críticos do mercado (Frete & Logística, Produção & Indústria, Consumo & Demanda, Preços & Mercado e Geopolítica & Comércio).
            3. **Análise Léxica Setorial:** Avalia termos de expansão e alívio operacional (*queda de custos, novos investimentos, parcerias, fluidez portuária*) versus gargalos e riscos (*alta de tarifas, quebra de oferta, sanções, embargos, estiagem*).
            4. **Pontuação Contínua:** Calcula a polaridade líquida numa escala de **-10.0 a +10.0 pontos**, classificando o barômetro em **Melhorando** (≥ +1.5 pts), **Estável** (-1.4 a +1.4 pts) ou **Piorando** (≤ -1.5 pts).
            """
        )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # FILTROS E BUSCA INTERATIVA
    # =========================================================================
    st.markdown("#### Filtros Setoriais")

    c_topic, c_nut, c_search = st.columns([1.5, 1.2, 1.8])

    topic_options = [
        "Todas as Notícias",
        "FRETE / LOGÍSTICA",
        "PRODUÇÃO",
        "CONSUMO / DEMANDA",
        "PREÇOS / MERCADO",
        "GEOPOLÍTICA / COMÉRCIO",
    ]

    with c_topic:
        sel_topic = st.selectbox("Filtrar por Tópico:", topic_options, index=0, key="news_topic_sel")

    nut_options = ["Todos os Nutrientes", "Nitrogenados (N)", "Fosfatados (P)", "Potássicos (K)", "Complexos NPK", "Geral"]
    with c_nut:
        sel_nut = st.selectbox("Filtrar por Nutriente:", nut_options, index=0, key="news_nut_sel")

    with c_search:
        search_kw = st.text_input(
            "Buscar por Palavra-Chave:",
            placeholder="Ex: Paranaguá, Petrobras, China, frete, soja...",
            key="news_kw_search",
        )

    # Aplicação dos filtros
    df_filtered = df_news.copy()

    if sel_topic != "Todas as Notícias":
        df_filtered = df_filtered[df_filtered["topic"] == sel_topic]

    if sel_nut != "Todos os Nutrientes":
        df_filtered = df_filtered[df_filtered["nutrient"] == sel_nut]

    if search_kw:
        kw = search_kw.strip().lower()
        mask = (
            df_filtered["title"].str.lower().str.contains(kw, na=False)
            | df_filtered["snippet"].str.lower().str.contains(kw, na=False)
            | df_filtered["source"].str.lower().str.contains(kw, na=False)
        )
        df_filtered = df_filtered[mask]

    # Ordenação garantida: matérias mais recentes sempre exibidas no topo
    if not df_filtered.empty and "published_at" in df_filtered.columns:
        df_filtered["_sort_dt"] = pd.to_datetime(df_filtered["published_at"], errors="coerce", utc=True)
        df_filtered = df_filtered.sort_values(by="_sort_dt", ascending=False).drop(columns=["_sort_dt"]).reset_index(drop=True)

    st.markdown(f"<div style='color: #4B5563; font-size: 0.88rem; margin: 0.5rem 0 1rem 0;'>Exibindo <b>{len(df_filtered)}</b> matérias dos últimos 7 dias (mais recentes primeiro):</div>", unsafe_allow_html=True)

    # =========================================================================
    # CARDS DE NOTÍCIAS EM DUAS COLUNAS PARALELAS
    # =========================================================================
    if df_filtered.empty:
        st.info("Nenhuma matéria encontrada com os filtros aplicados. Tente termos mais abrangentes.")
        return

    col_left, col_right = st.columns(2)

    for idx, (_, row) in enumerate(df_filtered.iterrows()):
        target_col = col_left if idx % 2 == 0 else col_right

        title = row.get("title", "Sem Título")
        link = row.get("link", "https://news.google.com")
        source = row.get("source", "Google Notícias")
        pub_rel = row.get("pub_date_relative", "Recente")
        snippet = row.get("snippet", "")
        topic = row.get("topic", "MERCADO GERAL")
        topic_color = row.get("topic_color", "emerald")
        nutrient = row.get("nutrient", "Geral")

        with target_col:
            st.markdown(
                f"""
                <div style="
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 12px;
                    padding: 1.25rem 1.35rem;
                    margin-bottom: 1.1rem;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
                    min-height: 240px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div>
                        <div style="display: flex; gap: 0.4rem; align-items: center; margin-bottom: 0.65rem; flex-wrap: wrap;">
                            <span class="fp-badge fp-badge-{topic_color}" style="font-size: 0.72rem;">{topic}</span>
                            <span class="fp-badge fp-badge-blue" style="font-size: 0.72rem;">{nutrient}</span>
                            <span style="font-size: 0.74rem; font-weight: 600; color: #1B4332; background: #EDF3EF; padding: 0.2rem 0.55rem; border-radius: 9999px;">
                                Fonte: {source}
                            </span>
                            <span style="font-size: 0.74rem; color: #6B7280; margin-left: auto;">
                                {pub_rel}
                            </span>
                        </div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #1B4332; line-height: 1.4; margin-bottom: 0.45rem;">
                            <a href="{link}" target="_blank" style="color: #1B4332; text-decoration: none;">
                                {title}
                            </a>
                        </div>
                        <div style="font-size: 0.85rem; color: #4B5563; line-height: 1.5; margin-bottom: 0.85rem;">
                            {snippet}
                        </div>
                    </div>
                    <div>
                        <a href="{link}" target="_blank" style="
                            display: inline-flex;
                            align-items: center;
                            gap: 0.35rem;
                            background: #F0F7F3;
                            border: 1px solid #B7E4C7;
                            color: #2D6A4F;
                            padding: 0.35rem 0.85rem;
                            border-radius: 8px;
                            font-size: 0.8rem;
                            font-weight: 600;
                            text-decoration: none;
                        ">
                            Acessar Matéria na Fonte Original
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    render_source_badge("Google News RSS Feed & Inteligência FertiPartner (Últimos 7 Dias)", "Agregador em Tempo Real")


if __name__ == "__main__":
    render_view()

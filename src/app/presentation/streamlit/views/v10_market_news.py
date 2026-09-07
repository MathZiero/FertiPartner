"""Radar de Notícias e Fatos Relevantes de Fertilizantes (Google News RSS)."""

import pandas as pd
import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
)
from app.presentation.streamlit.services.news_service import GoogleNewsService


def render_view() -> None:
    render_header(
        title="Radar de Notícias NPK • Google News",
        subtitle="Agregador e analisador em tempo real de notícias setoriais dos últimos 7 dias com alta correlação de mercado: capacidade produtiva, consumo de safras, fretes portuários, cotações e comércio internacional.",
        badge_text="Live Feed • AgTech",
        badge_type="emerald",
    )

    # Botão de atualização rápida do feed
    c_btn, c_note = st.columns([2.5, 5.5])
    with c_btn:
        if st.button("🔄 Recarregar Feed (Últimos 7 Dias)", width="stretch"):
            GoogleNewsService.fetch_fertilizer_news.clear()
            st.rerun()
    with c_note:
        st.caption("Filtro temporal estrito: apenas notícias publicadas nas últimas 168 horas (7 dias) com impacto direto no agronegócio de fertilizantes.")

    # Busca de notícias com cache inteligente
    df_news = GoogleNewsService.fetch_fertilizer_news()

    if df_news.empty:
        st.warning("Nenhuma notícia dos últimos 7 dias foi encontrada no momento. Tente novamente mais tarde.")
        return

    # =========================================================================
    # ANÁLISE DE SENTIMENTO SETORIAL (ÚLTIMOS 7 DIAS)
    # =========================================================================
    st.markdown("#### 🧭 Barômetro de Sentimento Setorial (Últimos 7 Dias)")
    st.caption("Diagnóstico automatizado de polaridade e tendências de mercado por tópico estratégico, calculado a partir das notícias publicadas nos últimos 7 dias.")

    sentiments = GoogleNewsService.analyze_sentiment_by_topic(df_news)

    # Grid de 5 colunas para os tópicos estratégicos
    cols = st.columns(len(sentiments))
    for idx, sent in enumerate(sentiments):
        with cols[idx]:
            with st.container(border=True):
                # Cabeçalho do card com ícone
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;">
                        <span style="font-size: 1.25rem;">{sent['icon']}</span>
                        <span style="font-size: 0.85rem; font-weight: 700; color: #1B4332; text-transform: uppercase;">
                            {sent['topic'].split(' / ')[0]}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Pontuação de sentimento em destaque (-10 a +10)
                score_color = "#2D6A4F" if sent["score_val"] >= 1.2 else ("#D97706" if sent["score_val"] <= -1.2 else "#2563EB")
                st.markdown(
                    f"""
                    <div style="margin: 0.35rem 0;">
                        <span style="font-size: 1.55rem; font-weight: 800; color: {score_color}; letter-spacing: -0.02em;">
                            {sent['score']}
                        </span>
                        <span style="font-size: 0.78rem; font-weight: 600; color: #6B7280;">/ 10 pts</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Classificação em 3 níveis (Melhorando / Estável / Piorando)
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.5rem;">
                        <span class="fp-badge fp-badge-{sent['badge_color']}" style="font-size: 0.72rem; padding: 0.2rem 0.6rem;">
                            {sent['classification']}
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #374151; font-weight: 600; line-height: 1.35; min-height: 2.3rem;">
                        {sent['status_label']}
                    </div>
                    <div style="font-size: 0.72rem; color: #6B7280; margin-top: 0.4rem; border-top: 1px dashed #E2E8F0; padding-top: 0.4rem;">
                        📰 <b>{sent['news_count']}</b> notícias nos últimos 7d
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # FILTROS E BUSCA INTERATIVA
    # =========================================================================
    st.markdown("#### 🔍 Filtros de Alta Correlação de Mercado")

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

    st.markdown(f"<div style='color: #4B5563; font-size: 0.88rem; margin: 0.5rem 0 1rem 0;'>Exibindo <b>{len(df_filtered)}</b> matérias dos últimos 7 dias:</div>", unsafe_allow_html=True)

    # =========================================================================
    # CARDS DE NOTÍCIAS ESTILIZADOS EM DUAS COLUNAS
    # =========================================================================
    if df_filtered.empty:
        st.info("Nenhuma notícia dos últimos 7 dias encontrada com os filtros selecionados. Tente termos mais amplos.")
        return

    # Distribuição em duas colunas paralelas (Grid Jornalístico AgTech)
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
                    min-height: 250px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div>
                        <div style="display: flex; gap: 0.4rem; align-items: center; margin-bottom: 0.65rem; flex-wrap: wrap;">
                            <span class="fp-badge fp-badge-{topic_color}" style="font-size: 0.72rem;">{topic}</span>
                            <span class="fp-badge fp-badge-blue" style="font-size: 0.72rem;">{nutrient}</span>
                            <span style="font-size: 0.74rem; font-weight: 600; color: #1B4332; background: #EDF3EF; padding: 0.2rem 0.55rem; border-radius: 9999px;">
                                📰 {source}
                            </span>
                            <span style="font-size: 0.74rem; color: #6B7280; margin-left: auto;">
                                🕒 {pub_rel}
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
                            Ler Matéria na Fonte Original ↗
                        </a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    render_source_badge("Google News RSS Feed & Inteligência FertiPartner (Últimos 7 Dias)", "Live Aggregator")


if __name__ == "__main__":
    render_view()

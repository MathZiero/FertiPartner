"""Radar de Notícias e Fatos Relevantes de Fertilizantes (Google News RSS)."""

import pandas as pd
import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
)
from app.presentation.streamlit.services.news_service import GoogleNewsService


def render_view() -> None:
    render_header(
        title="Radar de Notícias NPK • Google News",
        subtitle="Agregador e analisador em tempo real de notícias setoriais com alta correlação de mercado: capacidade produtiva, consumo de safras, fretes portuários, cotações e comércio internacional.",
        badge_text="Live Feed • AgTech",
        badge_type="emerald",
    )

    # Botão de atualização rápida do feed
    c_btn, _ = st.columns([2, 6])
    with c_btn:
        if st.button("🔄 Recarregar Feed de Notícias do Google", width="stretch"):
            GoogleNewsService.fetch_fertilizer_news.clear()
            st.rerun()

    # Busca de notícias com cache inteligente
    df_news = GoogleNewsService.fetch_fertilizer_news()

    if df_news.empty:
        st.warning("Não foi possível obter notícias no momento. Tente novamente mais tarde.")
        return

    # =========================================================================
    # KPI HERO CARDS: RADAR E TERMÔMETRO DE NOTÍCIAS
    # =========================================================================
    st.markdown("#### ⚡ Termômetro e Frequência do Setor")
    kpi_tot, kpi_rec, kpi_top, kpi_nut = st.columns(4)

    total_articles = len(df_news)
    recent_count = len(df_news[df_news["pub_date_relative"].isin(["Hoje", "Ontem", "Recente"]) | df_news["pub_date_relative"].str.contains("min|h", na=False)])
    top_topic = df_news["topic"].value_counts().index[0] if "topic" in df_news.columns and not df_news.empty else "Geral"
    nut_coverage = len(df_news["nutrient"].dropna().unique()) if "nutrient" in df_news.columns else 0

    with kpi_tot:
        render_kpi_card(
            title="Total Rastreado",
            value=f"{total_articles} notícias",
            help_text="Matérias curadas pelo mecanismo de busca setorial.",
        )
    with kpi_rec:
        render_kpi_card(
            title="Últimas 24-48 Horas",
            value=f"{recent_count} frescas",
            delta="Fluxo contínuo",
            delta_color="normal",
            help_text="Notícias publicadas nas últimas 48 horas.",
        )
    with kpi_top:
        render_kpi_card(
            title="Tópico em Evidência",
            value=top_topic.split(" / ")[0],
            help_text="Área com maior concentração de matérias recentes.",
        )
    with kpi_nut:
        render_kpi_card(
            title="Grupos Cobertos",
            value=f"{nut_coverage} classes",
            help_text="Nitrogenados, Fosfatados, Potássicos e Complexos NPK mapeados.",
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

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

    st.markdown(f"<div style='color: #4B5563; font-size: 0.88rem; margin: 0.5rem 0 1rem 0;'>Exibindo <b>{len(df_filtered)}</b> matérias filtradas:</div>", unsafe_allow_html=True)

    # =========================================================================
    # CARDS DE NOTÍCIAS ESTILIZADOS
    # =========================================================================
    if df_filtered.empty:
        st.info("Nenhuma notícia encontrada com os filtros selecionados. Tente termos mais amplos.")
        return

    for _, row in df_filtered.iterrows():
        title = row.get("title", "Sem Título")
        link = row.get("link", "https://news.google.com")
        source = row.get("source", "Google Notícias")
        pub_rel = row.get("pub_date_relative", "Recente")
        snippet = row.get("snippet", "")
        topic = row.get("topic", "MERCADO GERAL")
        topic_color = row.get("topic_color", "emerald")
        nutrient = row.get("nutrient", "Geral")

        st.markdown(
            f"""
            <div style="
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            ">
                <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap;">
                    <span class="fp-badge fp-badge-{topic_color}">{topic}</span>
                    <span class="fp-badge fp-badge-blue">{nutrient}</span>
                    <span style="font-size: 0.78rem; font-weight: 600; color: #1B4332; background: #EDF3EF; padding: 0.2rem 0.6rem; border-radius: 9999px;">
                        📰 {source}
                    </span>
                    <span style="font-size: 0.78rem; color: #6B7280; margin-left: auto;">
                        🕒 {pub_rel}
                    </span>
                </div>
                <div style="font-size: 1.12rem; font-weight: 700; color: #1B4332; line-height: 1.4; margin-bottom: 0.4rem;">
                    <a href="{link}" target="_blank" style="color: #1B4332; text-decoration: none;">
                        {title}
                    </a>
                </div>
                <div style="font-size: 0.88rem; color: #4B5563; line-height: 1.5; margin-bottom: 0.8rem;">
                    {snippet}
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
                        font-size: 0.82rem;
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
    render_source_badge("Google News RSS Feed & Inteligência FertiPartner", "Live Aggregator")


if __name__ == "__main__":
    render_view()

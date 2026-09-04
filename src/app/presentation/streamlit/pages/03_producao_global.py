"""Página 3: Produção Global e Ranking Mundial de Produtores (RF03, RF15)."""

import sys
import streamlit as st
import plotly.express as px
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    render_download_csv_button,
)
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, FERTI_COLORS


def render_page() -> None:
    render_header(
        title="Produção Global & Ranking Mundial",
        subtitle="Mapeamento geográfico da produção mundial de fertilizantes, volume de síntese/extração e concentração de mercado.",
        badge_text="FAOSTAT RFB/RFN",
        badge_type="emerald",
    )

    df_prod = FertiDataService.get_global_production_rankings()

    if df_prod.empty:
        st.warning("Dados de produção global não disponíveis no momento.")
        return

    # Filtros na barra superior
    col_fert, col_year = st.columns([6, 6])
    with col_fert:
        fert_options = ["Todos"] + sorted(df_prod["fertilizer_name"].dropna().unique().tolist())
        selected_fert = st.selectbox("Selecione o Fertilizante:", fert_options, index=0, key="p03_fert_select")

    with col_year:
        years = sorted(df_prod["production_year"].dropna().unique().tolist(), reverse=True)
        selected_year = st.selectbox("Ano de Referência:", years, index=0, key="p03_year_select") if years else 2023

    # Aplicação de filtros
    filtered = df_prod[df_prod["production_year"] == selected_year]
    if selected_fert != "Todos":
        filtered = filtered[filtered["fertilizer_name"] == selected_fert]

    # KPIs de produção
    total_prod = filtered["standard_quantity_mt"].sum()
    top_producer = filtered.sort_values(by="standard_quantity_mt", ascending=False).iloc[0] if not filtered.empty else None

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card(
            title="Produção Total do Segmento",
            value=f"{total_prod / 1e6:,.2f} M MT",
            delta=f"Ano Base {selected_year}",
            delta_positive=True,
            help_text="Volume físico equivalente",
        )
    with c2:
        top_name = top_producer["country_name"] if top_producer is not None else "N/A"
        top_share = top_producer["global_market_share_pct"] if top_producer is not None else 0.0
        render_kpi_card(
            title="Líder Global de Produção",
            value=f"{top_name}",
            delta=f"{top_share:.1f}% Market Share",
            delta_positive=True,
            help_text="Maior polo de fornecimento",
        )
    with c3:
        n_countries = filtered["country_name"].nunique()
        render_kpi_card(
            title="Polos Produtores Mapeados",
            value=f"{n_countries} Países",
            delta="Alta Concentração",
            delta_positive=False,
            help_text="Diversificação de oferta",
        )

    st.write("")

    # Mapa Mundi Coroplético
    st.subheader("🌍 Mapa Global de Produção (Toneladas Métricas)")
    if not filtered.empty:
        fig_map = px.choropleth(
            filtered,
            locations="country_iso3",
            color="standard_quantity_mt",
            hover_name="country_name",
            hover_data={
                "standard_quantity_mt": ":,.0f",
                "global_market_share_pct": ":.2f",
                "country_iso3": False,
            },
            labels={
                "standard_quantity_mt": "Produção (MT)",
                "global_market_share_pct": "Market Share (%)",
            },
            color_continuous_scale="Viridis",
            projection="natural earth",
        )
        fig_map.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor="rgba(255,255,255,0.2)",
                bgcolor="rgba(0,0,0,0)",
                lakecolor="#0B0F19",
                landcolor="#1A2438",
            ),
            margin=dict(l=0, r=0, t=10, b=10),
            height=460,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#F1F5F9"),
        )
        st.plotly_chart(fig_map, width="stretch", config=get_default_plotly_config())

    # Gráfico de Barras do Ranking
    col_chart, col_tbl = st.columns([6, 6])
    with col_chart:
        st.subheader("🏆 Ranking dos Maiores Produtores")
        sorted_prod = filtered.sort_values(by="standard_quantity_mt", ascending=True)
        fig_bar = px.bar(
            sorted_prod,
            x="standard_quantity_mt",
            y="country_name",
            orientation="h",
            text="standard_quantity_mt",
            labels={"standard_quantity_mt": "Produção (MT)", "country_name": "País"},
            color="standard_quantity_mt",
            color_continuous_scale="Teal",
        )
        fig_bar.update_traces(
            texttemplate="%{x:,.0f} MT",
            textposition="inside",
        )
        apply_ferti_theme(fig_bar, height=360, show_legend=False)
        st.plotly_chart(fig_bar, width="stretch", config=get_default_plotly_config())

    with col_tbl:
        st.subheader("📊 Detalhamento e Market Share (%)")
        display_tbl = filtered[["rank_position", "country_name", "standard_quantity_mt", "global_market_share_pct"]].sort_values(by="rank_position")
        st.dataframe(
            display_tbl.rename(columns={
                "rank_position": "Posição",
                "country_name": "País",
                "standard_quantity_mt": "Volume (MT)",
                "global_market_share_pct": "Market Share",
            }),
            column_config={
                "Market Share": st.column_config.ProgressColumn(
                    "Participação Global (%)",
                    help="Percentual do volume total",
                    format="%.2f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Volume (MT)": st.column_config.NumberColumn(
                    "Volume (MT)",
                    format="%d MT",
                ),
            },
            width="stretch",
            hide_index=True,
        )
        render_download_csv_button(display_tbl, filename=f"producao_global_{selected_year}.csv", key="dl_p03_tbl")

    render_source_badge("FAOSTAT (Food and Agriculture Organization of the UN)", "Anual")


if __name__ == "__main__":
    render_page()

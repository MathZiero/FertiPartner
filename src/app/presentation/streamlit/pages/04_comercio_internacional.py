"""Página 4: Comércio Internacional: Importações e Exportações Globais (RF04, RF05)."""

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
from app.presentation.streamlit.theme import (
    apply_ferti_theme,
    get_default_plotly_config,
    format_currency_usd,
    format_metric_tons,
    FERTI_COLORS,
)


def render_page() -> None:
    render_header(
        title="Comércio Internacional (Importações & Exportações)",
        subtitle="Movimentação transfronteiriça de fertilizantes, valores aduaneiros (FOB/CIF) e preços médios praticados por corredor comercial.",
        badge_text="UN Comtrade & Comex",
        badge_type="purple",
    )

    df_trade = FertiDataService.get_bilateral_trade_flows()

    if df_trade.empty:
        st.warning("Dados de comércio internacional indisponíveis.")
        return

    # Controles de filtro
    c_flow, c_fert, c_year = st.columns([4, 4, 4])
    with c_flow:
        flow_options = ["Todos", "IMPORT", "EXPORT"]
        selected_flow = st.segmented_control("Sentido do Fluxo", flow_options, default="Todos", key="p04_flow_ctrl")

    with c_fert:
        fert_options = ["Todos"] + sorted(df_trade["fertilizer_name"].dropna().unique().tolist())
        selected_fert = st.selectbox("Fertilizante:", fert_options, key="p04_fert_select")

    with c_year:
        years = sorted(df_trade["trade_year"].dropna().unique().tolist(), reverse=True)
        selected_year = st.selectbox("Ano:", years, index=0, key="p04_year_select") if years else 2023

    # Filtragem
    filtered = df_trade[df_trade["trade_year"] == selected_year].copy()
    if selected_flow != "Todos":
        filtered = filtered[filtered["flow_type"] == selected_flow]
    if selected_fert != "Todos":
        filtered = filtered[filtered["fertilizer_name"] == selected_fert]

    # KPIs de comércio
    total_qty = filtered["total_quantity_mt"].sum()
    total_val = filtered["total_value_usd"].sum()
    avg_price = (total_val / total_qty) if total_qty > 0 else 0.0

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(
            title="Volume Comercializado",
            value=format_metric_tons(total_qty),
            delta=f"Ano {selected_year}",
            delta_positive=True,
            help_text="Volume físico total",
        )
    with k2:
        render_kpi_card(
            title="Valor Ad-Valorem Total",
            value=format_currency_usd(total_val),
            delta="Moeda Corrente",
            delta_positive=True,
            help_text="Valor CIF/FOB declarado",
        )
    with k3:
        render_kpi_card(
            title="Preço Médio Ponderado",
            value=f"$ {avg_price:,.2f} / MT",
            delta="Benchmark Global",
            delta_positive=None,
            help_text="Valor / Volume",
        )

    st.write("")

    col_orig, col_dest = st.columns([6, 6])
    with col_orig:
        st.subheader("🚢 Principais Países Exportadores (Origens)")
        exp_summary = filtered.groupby("exporter_country")["total_quantity_mt"].sum().reset_index()
        exp_summary = exp_summary.sort_values(by="total_quantity_mt", ascending=True).tail(8)
        fig_exp = px.bar(
            exp_summary,
            x="total_quantity_mt",
            y="exporter_country",
            orientation="h",
            labels={"total_quantity_mt": "Volume (MT)", "exporter_country": "País Exportador"},
            color="total_quantity_mt",
            color_continuous_scale="Blues",
        )
        fig_exp.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
        apply_ferti_theme(fig_exp, height=340, show_legend=False)
        st.plotly_chart(fig_exp, width="stretch", config=get_default_plotly_config())

    with col_dest:
        st.subheader("📥 Principais Mercados Compradores (Destinos)")
        imp_summary = filtered.groupby("importer_country")["total_quantity_mt"].sum().reset_index()
        imp_summary = imp_summary.sort_values(by="total_quantity_mt", ascending=True).tail(8)
        fig_imp = px.bar(
            imp_summary,
            x="total_quantity_mt",
            y="importer_country",
            orientation="h",
            labels={"total_quantity_mt": "Volume (MT)", "importer_country": "País Importador"},
            color="total_quantity_mt",
            color_continuous_scale="Teal",
        )
        fig_imp.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
        apply_ferti_theme(fig_imp, height=340, show_legend=False)
        st.plotly_chart(fig_imp, width="stretch", config=get_default_plotly_config())

    st.subheader("📑 Relações Comerciais Detalhadas")
    display_cols = ["fertilizer_name", "flow_type", "exporter_country", "importer_country", "total_quantity_mt", "total_value_usd", "avg_usd_per_mt"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "fertilizer_name": "Fertilizante",
            "flow_type": "Fluxo",
            "exporter_country": "Origem",
            "importer_country": "Destino",
            "total_quantity_mt": "Volume (MT)",
            "total_value_usd": "Valor ($ USD)",
            "avg_usd_per_mt": "Preço Médio ($/MT)",
        }),
        column_config={
            "Volume (MT)": st.column_config.NumberColumn(format="%d MT"),
            "Valor ($ USD)": st.column_config.NumberColumn(format="$ %d"),
            "Preço Médio ($/MT)": st.column_config.NumberColumn(format="$ %.2f"),
        },
        width="stretch",
        hide_index=True,
    )
    render_download_csv_button(filtered, filename=f"comercio_internacional_{selected_year}.csv", key="dl_p04_table")

    render_source_badge("UN Comtrade • MDIC Comex Stat", "Mensal")


if __name__ == "__main__":
    render_page()

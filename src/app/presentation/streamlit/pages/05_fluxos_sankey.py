"""Página 5: Fluxos Comerciais Bilaterais com Diagrama Sankey Interativo."""

import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
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
        title="Fluxos Comerciais Bilaterais (Diagrama Sankey)",
        subtitle="Mapeamento visual dinâmico dos fluxos de suprimento internacional conectando polos exportadores aos mercados consumidores.",
        badge_text="Corredores Logísticos",
        badge_type="emerald",
    )

    df_trade = FertiDataService.get_bilateral_trade_flows()

    if df_trade.empty:
        st.warning("Dados de fluxos bilaterais não disponíveis.")
        return

    # Controles
    c1, c2, c3 = st.columns([5, 4, 3])
    with c1:
        fert_options = ["Todos"] + sorted(df_trade["fertilizer_name"].dropna().unique().tolist())
        selected_fert = st.selectbox("Fertilizante:", fert_options, key="p05_fert_select")

    with c2:
        years = sorted(df_trade["trade_year"].dropna().unique().tolist(), reverse=True)
        selected_year = st.selectbox("Ano de Referência:", years, index=0, key="p05_year_select") if years else 2023

    with c3:
        metric_choice = st.radio(
            "Ponderação das Rotas:",
            ["Volume (MT)", "Valor ($ USD)"],
            horizontal=True,
            key="p05_metric_radio",
        )

    # Filtragem
    filtered = df_trade[df_trade["trade_year"] == selected_year].copy()
    if selected_fert != "Todos":
        filtered = filtered[filtered["fertilizer_name"] == selected_fert]

    # Agregação bilateral entre Exportador e Importador
    agg_col = "total_quantity_mt" if metric_choice == "Volume (MT)" else "total_value_usd"
    routes = filtered.groupby(["exporter_country", "importer_country"])[agg_col].sum().reset_index()
    routes = routes[routes[agg_col] > 0]

    if routes.empty:
        st.info("Nenhum fluxo bilateral encontrado para os filtros selecionados.")
        return

    # Construção dos nós e links
    exporters = sorted(routes["exporter_country"].unique().tolist())
    importers = sorted(routes["importer_country"].unique().tolist())

    node_labels = exporters + importers
    node_indices = {name: i for i, name in enumerate(node_labels)}

    sources = [node_indices[exp] for exp in routes["exporter_country"]]
    targets = [node_indices[imp] for imp in routes["importer_country"]]
    values = routes[agg_col].tolist()

    node_colors = []
    for i, name in enumerate(node_labels):
        if i < len(exporters):
            node_colors.append("#2563EB")  # Azul para Exportadores
        else:
            node_colors.append("#2D6A4F")  # Verde para Importadores

    link_colors = ["rgba(37, 99, 235, 0.22)" for _ in values]

    fig_sankey = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=18,
                    thickness=20,
                    line=dict(color="#CBD5E1", width=0.5),
                    label=[f"{name} ({'Origem' if i < len(exporters) else 'Destino'})" for i, name in enumerate(node_labels)],
                    color=node_colors,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    hovertemplate=(
                        "<b>Origem:</b> %{source.label}<br>"
                        "<b>Destino:</b> %{target.label}<br>"
                        + (
                            "<b>Volume:</b> %{value:,.0f} MT<extra></extra>"
                            if metric_choice == "Volume (MT)"
                            else "<b>Valor:</b> $ %{value:,.2f} USD<extra></extra>"
                        )
                    ),
                ),
            )
        ]
    )

    apply_ferti_theme(
        fig_sankey,
        title=f"Fluxos de Comércio ({selected_fert} - {selected_year})",
        height=540,
        show_legend=False,
    )
    fig_sankey.update_layout(margin=dict(l=20, r=20, t=60, b=20))

    st.plotly_chart(fig_sankey, width="stretch", config=get_default_plotly_config())

    st.subheader("🧭 Resumo das Rotas Comerciais Mais Ativas")
    routes_sorted = routes.sort_values(by=agg_col, ascending=False)
    st.dataframe(
        routes_sorted.rename(columns={
            "exporter_country": "País de Origem (Exportador)",
            "importer_country": "País de Destino (Importador)",
            agg_col: f"Total ({metric_choice})",
        }),
        column_config={
            f"Total ({metric_choice})": st.column_config.NumberColumn(
                format="%d MT" if metric_choice == "Volume (MT)" else "$ %d"
            )
        },
        width="stretch",
        hide_index=True,
    )

    render_source_badge("UN Comtrade • MDIC Comex Stat", "Mensal")


if __name__ == "__main__":
    render_page()

"""Mercado Brasileiro, Consumo Aparente e Dependência Estratégica."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    render_download_csv_button,
    render_units_legend,
)
from app.presentation.streamlit.theme import (
    apply_ferti_theme,
    get_default_plotly_config,
    format_metric_tons,
    FERTI_COLORS,
)


def render_view() -> None:
    render_header(
        title="Mercado Brasileiro & Dependência Estratégica",
        subtitle="Panorama nacional do suprimento de fertilizantes: consumo aparente, capacidade industrial interna, taxa de dependência e distribuição estadual.",
        badge_text="Brasil Focus",
        badge_type="blue",
    )

    df_dep = FertiDataService.get_brazil_external_dependency()
    df_uf = FertiDataService.get_brazil_uf_distribution()
    df_trade = FertiDataService.get_bilateral_trade_flows()

    if df_dep.empty:
        st.warning("Dados de mercado brasileiro indisponíveis.")
        return

    # Seletor de Ano ou Fertilizante
    c1, c2 = st.columns([6, 6])
    with c1:
        years = sorted(df_dep["ref_year"].dropna().unique().tolist(), reverse=True)
        selected_year = st.selectbox("Ano de Referência:", years, index=0) if years else 2024
    with c2:
        fert_options = ["Todos"] + sorted(df_dep["fertilizer_name"].dropna().unique().tolist())
        selected_fert = st.selectbox("Fertilizante:", fert_options)

    # Filtragem
    filtered = df_dep[df_dep["ref_year"] == selected_year].copy()
    if selected_fert != "Todos":
        filtered = filtered[filtered["fertilizer_name"] == selected_fert]

    # KPIs consolidados
    total_import = filtered["total_imports_mt"].sum()
    total_prod = filtered["national_production_mt"].sum()
    total_export = filtered["total_exports_mt"].sum()
    apparent_cons = (total_prod + total_import - total_export)
    dep_rate = (total_import / apparent_cons * 100) if apparent_cons > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            title="Consumo Aparente (BR)",
            value=format_metric_tons(apparent_cons),
            delta=f"Ano {selected_year}",
            delta_positive=True,
            help_text="Consumo aparente em Toneladas Métricas (MT = 1.000 kg)",
        )
    with k2:
        render_kpi_card(
            title="Importações Totais",
            value=format_metric_tons(total_import),
            delta=f"{total_import/apparent_cons*100:.1f}% da oferta" if apparent_cons > 0 else None,
            delta_positive=False,
            help_text="Volume total internalizado em Toneladas Métricas (MT)",
        )
    with k3:
        render_kpi_card(
            title="Produção Nacional",
            value=format_metric_tons(total_prod),
            delta=f"{total_prod/apparent_cons*100:.1f}% da oferta" if apparent_cons > 0 else None,
            delta_positive=True,
            help_text="Produção industrial brasileira em Toneladas Métricas (MT)",
        )
    with k4:
        render_kpi_card(
            title="Taxa de Dependência Externa",
            value=f"{dep_rate:.1f}%",
            delta="Alerta Estratégico",
            delta_positive=False if dep_rate > 70 else True,
            help_text="Meta Plano Nac. Fertilizantes: <50%",
        )

    st.divider()

    # Alerta se houver dados pendentes de consolidação no ano selecionado
    if not filtered.empty and "is_consolidated" in filtered.columns:
        incomplete_items = filtered[~filtered["is_consolidated"]]
        if not incomplete_items.empty:
            st.info(
                f"ℹ️ **Aviso Metodológico ({selected_year}):** Existem produtos aguardando consolidação final de censo de produção nacional (FAO/ANDA). A dependência externa e o consumo aparente são calculados exclusivamente sobre séries consolidadas para evitar distorções."
            )

    tab_balance, tab_geo, tab_suppliers = st.tabs([
        "⚖️ Balanço Oferta & Demanda",
        "🗺️ Distribuição por Estado (UF)",
        "🌐 Principais Países Fornecedores",
    ])

    with tab_balance:
        c_bar, c_dep_ind = st.columns([7, 5])
        with c_bar:
            c_b_title, c_b_opt = st.columns([7, 5])
            with c_b_title:
                st.markdown("##### 📦 Balanço Físico: Produção vs. Importações")
            with c_b_opt:
                bar_mode = st.radio(
                    "Exibição:",
                    ["Empilhado", "Lado a Lado"],
                    horizontal=True,
                    key="p07_barmode_toggle",
                )

            fig_bal = px.bar(
                filtered,
                x="fertilizer_name",
                y=["national_production_mt", "total_imports_mt"],
                barmode="stack" if bar_mode == "Empilhado" else "group",
                labels={"value": "Volume (MT)", "fertilizer_name": "Produto", "variable": "Tipo de Oferta"},
                color_discrete_map={
                    "national_production_mt": "#10B981",
                    "total_imports_mt": "#3B82F6",
                },
            )
            fig_bal.for_each_trace(lambda t: t.update(
                name="Produção Nacional" if "national_production" in t.name else "Importações"
            ))
            apply_ferti_theme(fig_bal, height=360)
            st.plotly_chart(fig_bal, width="stretch", config=get_default_plotly_config())

        with c_dep_ind:
            st.markdown("##### 🚨 Taxa de Dependência Externa por Fertilizante (%)")
            # Filtra apenas registros consolidados com dependência válida
            filtered_dep = filtered.dropna(subset=["external_dependency_pct"])
            if not filtered_dep.empty:
                fig_gauge = px.bar(
                    filtered_dep,
                    x="external_dependency_pct",
                    y="fertilizer_name",
                    orientation="h",
                    color="external_dependency_pct",
                    color_continuous_scale=["#10B981", "#F59E0B", "#F43F5E"],
                    range_color=[50, 100],
                    labels={"external_dependency_pct": "Dependência (%)", "fertilizer_name": "Produto"},
                )
                fig_gauge.update_traces(texttemplate="%{x:.1f}%", textposition="inside")
                apply_ferti_theme(fig_gauge, height=360, show_legend=False)
                st.plotly_chart(fig_gauge, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Taxa de dependência não calculada para os filtros selecionados (aguardando dados consolidados de produção).")

    with tab_geo:
        st.markdown("##### 🚜 Participação dos Estados no Consumo / Internalização de Fertilizantes")
        c_uf_chart, c_uf_table = st.columns([7, 5])
        with c_uf_chart:
            if not df_uf.empty and "share_pct" in df_uf.columns:
                df_uf_sorted = df_uf.sort_values(by="share_pct", ascending=True)
                fig_uf = px.bar(
                    df_uf_sorted,
                    x="share_pct",
                    y="uf",
                    orientation="h",
                    labels={"share_pct": "Participação (%)", "uf": "Estado (UF)"},
                    color="share_pct",
                    color_continuous_scale="Viridis",
                )
                fig_uf.update_traces(texttemplate="%{x:.1f}%", textposition="inside")
                apply_ferti_theme(fig_uf, height=380, show_legend=False)
                st.plotly_chart(fig_uf, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Distribuição por UF não disponível.")

        with c_uf_table:
            st.markdown("###### Ranking dos Principais Estados Consumidores")
            if not df_uf.empty:
                st.dataframe(
                    df_uf.rename(columns={
                        "uf": "UF",
                        "state_name": "Estado",
                        "share_pct": "Participação (%)",
                        "quantity_mt": "Volume Estimado (MT)",
                    }),
                    column_config={
                        "Participação (%)": st.column_config.ProgressColumn(
                            "Participação (%)",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "Volume Estimado (MT)": st.column_config.NumberColumn(format="%d MT"),
                    },
                    width="stretch",
                    hide_index=True,
                )

    with tab_suppliers:
        st.markdown("##### 🚢 Origem das Importações do Brasil por País Parceiro")
        br_imports = df_trade[
            (df_trade["importer_country"] == "Brasil") | (df_trade["importer_iso3"] == "BRA")
        ]
        if not br_imports.empty:
            supp_agg = br_imports.groupby("exporter_country")["total_quantity_mt"].sum().reset_index()
            supp_agg = supp_agg.sort_values(by="total_quantity_mt", ascending=False)
            fig_supp = px.pie(
                supp_agg,
                names="exporter_country",
                values="total_quantity_mt",
                hole=0.5,
                color_discrete_sequence=FERTI_COLORS,
            )
            fig_supp.update_traces(textinfo="percent+label", textposition="inside")
            apply_ferti_theme(fig_supp, height=360, show_legend=False)
            st.plotly_chart(fig_supp, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Registros de fornecedores do Brasil não encontrados.")

    st.divider()
    st.markdown("##### 📋 Tabela Consolidada de Dependência Comercial")
    st.dataframe(
        filtered.rename(columns={
            "fertilizer_name": "Fertilizante",
            "ref_year": "Ano",
            "national_production_mt": "Produção Nacional (MT)",
            "total_imports_mt": "Importações (MT)",
            "total_exports_mt": "Exportações (MT)",
            "apparent_consumption_mt": "Consumo Aparente (MT)",
            "external_dependency_pct": "Dependência (%)",
        }),
        column_config={
            "Produção Nacional (MT)": st.column_config.NumberColumn(format="%d MT"),
            "Importações (MT)": st.column_config.NumberColumn(format="%d MT"),
            "Consumo Aparente (MT)": st.column_config.NumberColumn(format="%d MT"),
            "Dependência (%)": st.column_config.ProgressColumn(
                "Dependência (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
        width="stretch",
        hide_index=True,
    )
    render_download_csv_button(filtered, filename="dependencia_brasil.csv")

    st.divider()
    render_units_legend()
    render_source_badge("MDIC Comex Stat • ANDA • FAOSTAT", "Mensal")


if __name__ == "__main__":
    render_view()

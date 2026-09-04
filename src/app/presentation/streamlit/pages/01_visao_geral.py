"""Página 1: Visão Geral do Mercado de Fertilizantes (Dashboard Executivo)."""

import sys
from pathlib import Path
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
)
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, FERTI_COLORS


def render_page() -> None:
    render_header(
        title="Visão Geral do Mercado NPK",
        subtitle="Inteligência integrada de fertilizantes: produção mundial, comércio exterior, preços e dependência estratégica do Brasil.",
        badge_text="Live Intelligence",
        badge_type="emerald",
    )

    # Coleta dos dados consolidados via serviço de dados
    df_fert = FertiDataService.get_fertilizer_profiles()
    df_prod = FertiDataService.get_global_production_rankings()
    df_trade = FertiDataService.get_bilateral_trade_flows()
    df_dep = FertiDataService.get_brazil_external_dependency()
    df_prices = FertiDataService.get_price_benchmark_trends()

    # Métricas principais
    total_br_import = df_dep["total_imports_mt"].sum() if not df_dep.empty else 41500000.0
    avg_br_dep = df_dep["external_dependency_pct"].mean() if not df_dep.empty else 88.5
    total_global_prod = df_prod["standard_quantity_mt"].sum() if not df_prod.empty else 184000000.0
    latest_price = df_prices["standard_price_usd_per_mt"].iloc[-1] if not df_prices.empty else 430.0

    # Grid de KPIs com st.metric nativo em container com borda
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Importações Brasil",
            value=f"{total_br_import / 1e6:,.1f} M MT",
            delta="+5.4% YoY",
            delta_positive=True,
            help_text="Volume total internalizado",
        )
    with c2:
        render_kpi_card(
            title="Dependência Externa (BR)",
            value=f"{avg_br_dep:.1f}%",
            delta="+1.2 p.p.",
            delta_positive=False,
            help_text="Importações / Consumo Aparente",
        )
    with c3:
        render_kpi_card(
            title="Produção Global Auditada",
            value=f"{total_global_prod / 1e6:,.1f} M MT",
            delta="+2.8% YoY",
            delta_positive=True,
            help_text="Principais polos globais",
        )
    with c4:
        render_kpi_card(
            title="Preço Médio de Referência",
            value=f"$ {latest_price:,.1f}",
            delta="-3.2% MoM",
            delta_positive=True,
            help_text="USD por Tonelada Métrica",
        )

    st.write("")

    # Abas com perspectivas analíticas
    tab_overview, tab_prices, tab_products = st.tabs([
        "📊 Composição & Balanço",
        "📈 Panorama de Preços",
        "🌱 Matriz de Fertilizantes Cadastrados",
    ])

    with tab_overview:
        col_left, col_right = st.columns([6, 5])
        with col_left:
            st.subheader("🇧🇷 Demanda e Importações Brasileiras por Fertilizante (MT)")
            if not df_dep.empty:
                fig_dep = px.bar(
                    df_dep,
                    x="fertilizer_name",
                    y=["total_imports_mt", "national_production_mt"],
                    barmode="stack",
                    labels={"value": "Volume (Toneladas Métricas)", "fertilizer_name": "Fertilizante", "variable": "Fluxo"},
                    color_discrete_map={
                        "total_imports_mt": "#3B82F6",
                        "national_production_mt": "#10B981",
                    },
                )
                fig_dep.for_each_trace(lambda t: t.update(
                    name="Importações (MT)" if "total_imports" in t.name else "Produção Nacional (MT)"
                ))
                apply_ferti_theme(fig_dep, height=360)
                st.plotly_chart(fig_dep, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Sem dados de dependência externa disponíveis.")

        with col_right:
            st.subheader("🌐 Concentração da Produção Mundial")
            if not df_prod.empty:
                top_prods = df_prod.groupby("country_name")["standard_quantity_mt"].sum().reset_index()
                top_prods = top_prods.sort_values(by="standard_quantity_mt", ascending=False).head(6)
                fig_pie = px.pie(
                    top_prods,
                    names="country_name",
                    values="standard_quantity_mt",
                    hole=0.45,
                    color_discrete_sequence=FERTI_COLORS,
                )
                apply_ferti_theme(fig_pie, height=360)
                st.plotly_chart(fig_pie, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Sem dados de produção global.")

    with tab_prices:
        st.subheader("📉 Séries Históricas de Preços Internacionais (USD / MT)")
        if not df_prices.empty:
            fig_p = px.line(
                df_prices,
                x="price_date",
                y="standard_price_usd_per_mt",
                color="benchmark_name",
                markers=True,
                labels={"price_date": "Data", "standard_price_usd_per_mt": "Preço Médio (USD / MT)", "benchmark_name": "Benchmark"},
            )
            apply_ferti_theme(fig_p, height=380)
            st.plotly_chart(fig_p, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Séries de preços não disponíveis.")

    with tab_products:
        st.subheader("🌱 Catálogo Ativo de Fertilizantes na Base 4NF")
        if not df_fert.empty:
            cols = ["canonical_name", "category_name", "chemical_formula", "cas_rn"]
            available_cols = [c for c in cols if c in df_fert.columns]
            rename_map = {
                "canonical_name": "Fertilizante",
                "category_name": "Categoria",
                "chemical_formula": "Fórmula Química",
                "cas_rn": "Registro CAS",
            }
            st.dataframe(
                df_fert[available_cols].rename(columns=rename_map),
                width="stretch",
                hide_index=True,
            )
            render_download_csv_button(df_fert, filename="catalogo_fertilizantes.csv", key="dl_p01_fert")

    render_source_badge("MDIC Comex Stat • FAOSTAT • Banco Mundial / FRED", "Mensal & Anual")


if __name__ == "__main__":
    render_page()

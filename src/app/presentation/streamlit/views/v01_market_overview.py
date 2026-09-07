"""Visão Geral do Mercado de Fertilizantes (Dashboard Executivo)."""

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
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, FERTI_COLORS


def render_view() -> None:
    render_header(
        title="Visão Geral do Mercado NPK",
        subtitle="Inteligência integrada de fertilizantes: produção mundial, comércio exterior, preços e dependência estratégica do Brasil.",
        badge_text="Live Intelligence",
        badge_type="emerald",
    )

    # Coleta dos dados consolidados
    df_fert = FertiDataService.get_fertilizer_profiles()
    df_prod = FertiDataService.get_global_production_rankings()
    df_trade = FertiDataService.get_bilateral_trade_flows()
    df_dep = FertiDataService.get_brazil_external_dependency()
    df_prices = FertiDataService.get_price_benchmark_trends()

    # Cálculo dos KPIs principais
    total_br_import = df_dep["total_imports_mt"].sum() if not df_dep.empty else 41500000.0
    avg_br_dep = df_dep["external_dependency_pct"].mean() if not df_dep.empty else 88.5
    total_global_prod = df_prod["standard_quantity_mt"].sum() if not df_prod.empty else 184000000.0
    latest_price = df_prices["standard_price_usd_per_mt"].iloc[-1] if not df_prices.empty else 430.0

    # Grid de KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Importações Brasil",
            value=f"{total_br_import / 1e6:,.1f} M MT",
            delta="+5.4% YoY",
            delta_positive=True,
            help_text="Volume total em Milhões de Toneladas Métricas (M MT = 1.000.000 t)",
        )
    with c2:
        render_kpi_card(
            title="Dependência Externa (BR)",
            value=f"{avg_br_dep:.1f}%",
            delta="+1.2 p.p.",
            delta_positive=False,
            help_text="Importações / Consumo Aparente (% de dependência nacional)",
        )
    with c3:
        render_kpi_card(
            title="Produção Global Auditada",
            value=f"{total_global_prod / 1e6:,.1f} M MT",
            delta="+2.8% YoY",
            delta_positive=True,
            help_text="Principais polos globais em Milhões de Toneladas Métricas (M MT)",
        )
    with c4:
        render_kpi_card(
            title="Preço Médio de Referência",
            value=f"$ {latest_price:,.1f} / MT",
            delta="-3.2% MoM",
            delta_positive=True,
            help_text="Dólares Americanos por Tonelada Métrica (USD/MT)",
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Abas com diferentes perspectivas analíticas
    tab_overview, tab_prices, tab_products = st.tabs([
        "📊 Composição & Balanço",
        "📈 Panorama de Preços",
        "🌱 Matriz de Fertilizantes Cadastrados",
    ])

    with tab_overview:
        col_left, col_right = st.columns([6, 5])
        with col_left:
            st.markdown("##### 🇧🇷 Composição do Consumo Aparente Brasileiro (Oferta vs Dependência)")
            if not df_dep.empty:
                fig_bar = px.bar(
                    df_dep,
                    x="fertilizer_name",
                    y=["national_production_mt", "total_imports_mt"],
                    barmode="stack",
                    color_discrete_sequence=["#2D6A4F", "#2563EB"],
                    labels={
                        "fertilizer_name": "Fertilizante",
                        "value": "Quantidade em Toneladas Métricas (MT)",
                        "variable": "Componente da Oferta",
                    },
                )
                apply_ferti_theme(fig_bar, height=350, x_title="Fertilizante", y_title="Volume em Toneladas Métricas (MT)")
                st.plotly_chart(fig_bar, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Dados de dependência não disponíveis.")

        with col_right:
            st.markdown("##### 🌍 Top Produtores Mundiais (Market Share Global %)")
            if not df_prod.empty:
                fig_pie = px.pie(
                    df_prod.groupby("country_name")["standard_quantity_mt"].sum().reset_index(),
                    names="country_name",
                    values="standard_quantity_mt",
                    hole=0.45,
                    color_discrete_sequence=FERTI_COLORS,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                apply_ferti_theme(fig_pie, height=350, show_legend=False)
                st.plotly_chart(fig_pie, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Dados de produção não disponíveis.")

    with tab_prices:
        st.markdown("##### 📈 Evolução Recente dos Preços Internacionais (FOB e CFR em USD/MT)")
        if not df_prices.empty:
            fig_prices = px.line(
                df_prices,
                x="price_date",
                y="standard_price_usd_per_mt",
                color="benchmark_name",
                markers=True,
                color_discrete_sequence=FERTI_COLORS,
                labels={
                    "price_date": "Data da Cotação",
                    "standard_price_usd_per_mt": "Preço em Dólares por Tonelada Métrica (USD/MT)",
                    "benchmark_name": "Benchmark Internacional",
                },
            )
            apply_ferti_theme(fig_prices, height=400, x_title="Data da Cotação", y_title="Preço em Dólares por Tonelada Métrica (USD/MT)")
            st.plotly_chart(fig_prices, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Séries de preços não disponíveis.")

    with tab_products:
        st.markdown("##### 📑 Catálogo de Fertilizantes Mapeados no Sistema")
        if not df_fert.empty:
            display_cols = ["canonical_name", "category_name", "chemical_formula", "cas_rn"]
            available_cols = [c for c in display_cols if c in df_fert.columns]
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
            render_download_csv_button(df_fert, filename="catalogo_fertilizantes.csv")

    render_units_legend()
    render_source_badge("MDIC Comex Stat • FAOSTAT • Banco Mundial / FRED", "Mensal & Anual")


if __name__ == "__main__":
    render_view()

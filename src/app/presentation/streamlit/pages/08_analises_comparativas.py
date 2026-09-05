"""Página 8: Análise Comparativa e Correlações entre Fertilizantes e Países."""

import sys
import streamlit as st
import plotly.express as px
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
    FERTI_COLORS,
)


def render_page() -> None:
    render_header(
        title="Análise Comparativa & Correlações",
        subtitle="Mecanismo de inteligência para benchmark comparativo entre múltiplos fertilizantes ou países (produção, preços e participação de mercado).",
        badge_text="Análise Comparada",
        badge_type="purple",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()
    df_prod = FertiDataService.get_global_production_rankings()
    df_prices = FertiDataService.get_price_benchmark_trends()

    tab_fert_comp, tab_country_comp = st.tabs([
        "🌱 Comparador de Fertilizantes (NPK)",
        "🌐 Comparador entre Países",
    ])

    with tab_fert_comp:
        st.subheader("🧪 Selecione os Produtos para Comparação Multidimensional")
        fert_list = df_fert["canonical_name"].tolist() if not df_fert.empty else ["Ureia", "Fosfato Monoamônico (MAP)", "Cloreto de Potássio (KCl / MOP)"]
        default_selected = fert_list[:3] if len(fert_list) >= 3 else fert_list
        selected_ferts = st.multiselect("Fertilizantes Selecionados:", fert_list, default=default_selected, key="p08_ferts_multi")

        if not selected_ferts:
            st.info("Selecione ao menos um fertilizante para análise.")
            return

        # Comparação de Preços no Período
        st.markdown("###### 📈 Comparativo de Trajetória de Preços (USD / MT)")
        comp_prices = df_prices[df_prices["fertilizer_name"].isin(selected_ferts)]
        if not comp_prices.empty:
            fig_p_comp = px.line(
                comp_prices,
                x="price_date",
                y="standard_price_usd_per_mt",
                color="benchmark_name",
                markers=True,
                labels={"price_date": "Data", "standard_price_usd_per_mt": "Preço (USD/MT)", "benchmark_name": "Benchmark"},
            )
            apply_ferti_theme(
                fig_p_comp,
                height=380,
                x_title="Data da Cotação",
                y_title="Preço de Referência (USD / MT)",
            )
            st.plotly_chart(fig_p_comp, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Preços indisponíveis para os fertilizantes selecionados.")

        # Tabela comparativa de especificações
        st.markdown("###### 📊 Comparativo Técnico de Composição")
        comp_spec = df_fert[df_fert["canonical_name"].isin(selected_ferts)].copy()
        if not comp_spec.empty:
            comp_spec["garantia_nutricional"] = comp_spec["typical_nutrients"].apply(
                lambda x: ", ".join([f"{k}: {v}%" for k, v in x.items()]) if isinstance(x, dict) else "-"
            )
            st.dataframe(
                comp_spec[["canonical_name", "category_name", "chemical_formula", "cas_rn", "garantia_nutricional"]].rename(columns={
                    "canonical_name": "Produto",
                    "category_name": "Categoria",
                    "chemical_formula": "Fórmula",
                    "cas_rn": "CAS RN",
                    "garantia_nutricional": "Garantia Típica",
                }),
                width="stretch",
                hide_index=True,
            )

    with tab_country_comp:
        st.subheader("🌍 Comparativo de Produção e Escala Industrial por País")
        all_countries = sorted(df_prod["country_name"].dropna().unique().tolist()) if not df_prod.empty else ["Brasil", "China", "Índia", "Canadá"]
        def_countries = [c for c in ["China", "Índia", "Canadá", "Brasil"] if c in all_countries]
        selected_countries = st.multiselect("Países Selecionados:", all_countries, default=def_countries if def_countries else all_countries[:3], key="p08_countries_multi")

        if selected_countries and not df_prod.empty:
            country_df = df_prod[df_prod["country_name"].isin(selected_countries)]
            fig_country = px.bar(
                country_df,
                x="country_name",
                y="standard_quantity_mt",
                color="fertilizer_name",
                barmode="group",
                labels={"standard_quantity_mt": "Produção (MT)", "country_name": "País", "fertilizer_name": "Fertilizante"},
            )
            apply_ferti_theme(
                fig_country,
                height=400,
                x_title="País de Origem",
                y_title="Volume de Produção (Toneladas Métricas)",
            )
            st.plotly_chart(fig_country, width="stretch", config=get_default_plotly_config())

            st.dataframe(
                country_df[["country_name", "fertilizer_name", "production_year", "standard_quantity_mt", "global_market_share_pct"]].rename(columns={
                    "country_name": "País",
                    "fertilizer_name": "Produto",
                    "production_year": "Ano",
                    "standard_quantity_mt": "Produção (MT)",
                    "global_market_share_pct": "Market Share (%)",
                }),
                column_config={
                    "Produção (MT)": st.column_config.NumberColumn(format="%d MT"),
                    "Market Share (%)": st.column_config.NumberColumn(format="%.2f%%"),
                },
                width="stretch",
                hide_index=True,
            )

    render_source_badge("Séries Oficiais Homologadas", "Consolidado")


if __name__ == "__main__":
    render_page()

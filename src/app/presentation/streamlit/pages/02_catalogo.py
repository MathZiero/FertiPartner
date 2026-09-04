"""Página 2: Catálogo e Perfil Detalhado de Fertilizantes (RF01, RF02, RF21)."""

import sys
import streamlit as st
import plotly.express as px
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
    show_fertilizer_details_modal,
    render_download_csv_button,
)
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, NUTRIENT_COLORS


def render_page() -> None:
    render_header(
        title="Catálogo & Perfil dos Fertilizantes",
        subtitle="Especificações físico-químicas, concentração nutricional (N, P2O5, K2O, S), códigos aduaneiros (NCM/HS) e sinônimos de mercado.",
        badge_text="4NF Catalog",
        badge_type="blue",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()

    if df_fert.empty:
        st.warning("Nenhum fertilizante cadastrado.")
        return

    # Seletor de categoria
    categories = ["Todas"] + sorted(df_fert["category_name"].dropna().unique().tolist())
    selected_cat = st.segmented_control("Filtrar por Categoria", categories, default="Todas", key="p02_cat_filter")

    filtered_df = df_fert if selected_cat == "Todas" else df_fert[df_fert["category_name"] == selected_cat]

    # Grid de produtos
    col_select, col_details = st.columns([4, 8])

    with col_select:
        st.subheader("📌 Seleção de Produto")
        fert_options = filtered_df["canonical_name"].tolist()
        if not fert_options:
            st.info("Nenhum produto nesta categoria.")
            return

        selected_fert_name = st.selectbox("Fertilizante:", fert_options, index=0, key="p02_fert_select")
        fert_row = filtered_df[filtered_df["canonical_name"] == selected_fert_name].iloc[0].to_dict()

        with st.container(border=True):
            st.markdown(f"### {fert_row.get('canonical_name')}")
            st.caption(fert_row.get("category_name", "N/A"))
            st.divider()
            st.markdown(f"**Fórmula:** `{fert_row.get('chemical_formula', 'N/A')}`")
            st.markdown(f"**CAS RN:** `{fert_row.get('cas_rn', 'N/A')}`")

            if st.button("🔍 Ver Ficha Técnica Completa", key="btn_p02_modal"):
                show_fertilizer_details_modal(fert_row)

    with col_details:
        st.subheader("🧪 Composição Nutricional e Descrição")
        st.write(fert_row.get("description", "Sem descrição disponível."))

        c_nut, c_tax = st.columns([6, 6])
        with c_nut:
            with st.container(border=True):
                st.markdown("###### Concentração Nutricional Típica (%)")
                nutrients = fert_row.get("typical_nutrients") or {}
                if isinstance(nutrients, dict) and nutrients:
                    nut_df = pd.DataFrame([{"Nutriente": k, "Teor (%)": float(v)} for k, v in nutrients.items()])
                    fig_nut = px.pie(
                        nut_df,
                        names="Nutriente",
                        values="Teor (%)",
                        hole=0.55,
                        color="Nutriente",
                        color_discrete_map=NUTRIENT_COLORS,
                    )
                    fig_nut.update_traces(
                        textposition="inside",
                        textinfo="label+value",
                        texttemplate="%{label}: %{value:.1f}%",
                    )
                    apply_ferti_theme(fig_nut, height=250, show_legend=False)
                    st.plotly_chart(fig_nut, width="stretch", config=get_default_plotly_config())
                else:
                    st.info("Composição nutricional não declarada.")

        with c_tax:
            with st.container(border=True):
                st.markdown("###### Classificações Aduaneiras (NCM / HS)")
                codes = fert_row.get("hs_ncm_codes") or []
                if codes:
                    for c in codes:
                        st.markdown(f"- Código Tarifa: `NCM/HS {c}`")
                else:
                    st.write("Sem códigos associados.")

                st.markdown("###### Sinônimos e Nomes de Mercado")
                syns = fert_row.get("synonyms") or []
                if syns:
                    st.markdown(", ".join([f"`{s}`" for s in syns]))
                else:
                    st.write("Nenhum sinônimo comercial cadastrado.")

    st.divider()
    st.subheader("📋 Matriz Comparativa de Fertilizantes")

    df_table = df_fert.copy()
    df_table["nutrientes_resumo"] = df_table["typical_nutrients"].apply(
        lambda x: ", ".join([f"{k}: {v}%" for k, v in x.items()]) if isinstance(x, dict) else "-"
    )

    st.dataframe(
        df_table[["canonical_name", "category_name", "chemical_formula", "cas_rn", "nutrientes_resumo"]].rename(
            columns={
                "canonical_name": "Produto",
                "category_name": "Categoria",
                "chemical_formula": "Fórmula",
                "cas_rn": "CAS RN",
                "nutrientes_resumo": "Garantia Nutricional",
            }
        ),
        width="stretch",
        hide_index=True,
    )
    render_download_csv_button(df_table, filename="catalogo_completo.csv", key="dl_p02_table")

    render_source_badge("Catálogo Mapeado FertiPartner • Base 4NF", "Cadastral")


if __name__ == "__main__":
    render_page()

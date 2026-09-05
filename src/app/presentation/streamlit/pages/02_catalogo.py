"""Página 2: Catálogo Físico-Químico e Agronômico de Fertilizantes."""

import sys
import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
    show_fertilizer_details_modal,
)


def render_page() -> None:
    render_header(
        title="Catálogo & Perfil dos Fertilizantes",
        subtitle="Especificações físico-químicas, teores nutricionais garantidos (N, P2O5, K2O, S), códigos aduaneiros (NCM/HS) e sinônimos comerciais de mercado.",
        badge_text="Catálogo Oficial",
        badge_type="emerald",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()

    if df_fert.empty:
        st.warning("Nenhum fertilizante cadastrado no catálogo.")
        return

    # Lista de categorias disponíveis (SEM a opção 'Todas' / 'Todos')
    raw_categories = sorted(df_fert["category_name"].dropna().unique().tolist())
    if not raw_categories:
        st.warning("Nenhuma categoria identificada.")
        return

    # Seletor de categoria direto e intuitivo
    selected_cat = st.segmented_control(
        "Selecione a Categoria de Fertilizantes:",
        raw_categories,
        default=raw_categories[0],
        key="p02_cat_filter",
    )
    if not selected_cat:
        selected_cat = raw_categories[0]

    # Filtragem obrigatória pela categoria selecionada
    filtered_df = df_fert[df_fert["category_name"] == selected_cat].copy()

    st.write("")
    st.markdown(f"#### 📦 Fertilizantes Disponíveis em *{selected_cat}* ({len(filtered_df)} itens)")

    if filtered_df.empty:
        st.info("Nenhum produto cadastrado nesta categoria.")
        return

    # Exibição de todos os produtos da categoria em cards estruturados e elegantes
    for idx, row in filtered_df.iterrows():
        fert_dict = row.to_dict()
        canonical_name = fert_dict.get("canonical_name", "Fertilizante")
        formula = fert_dict.get("chemical_formula", "N/A")
        cas = fert_dict.get("cas_rn", "N/A")
        description = fert_dict.get("description", "Sem descrição disponível.")
        nutrients = fert_dict.get("typical_nutrients") or {}
        codes = fert_dict.get("hs_ncm_codes") or []
        synonyms = fert_dict.get("synonyms") or []

        with st.container(border=True):
            col_main, col_side = st.columns([8, 4])

            with col_main:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 0.35rem;">
                        <h3 style="margin: 0; color: #1B4332; font-size: 1.4rem;">{canonical_name}</h3>
                        <span style="background-color: #EDF3EF; color: #2D6A4F; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 6px;">Fórmula: {formula}</span>
                        <span style="background-color: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 500; padding: 2px 8px; border-radius: 6px;">CAS: {cas}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write(description)

                # Classificações aduaneiras e sinônimos agrupados
                details_left, details_right = st.columns(2)
                with details_left:
                    st.markdown("**Códigos Aduaneiros (NCM / HS):**")
                    if codes:
                        st.markdown(" ".join([f"`{c}`" for c in codes]))
                    else:
                        st.caption("Sem código associado")

                with details_right:
                    st.markdown("**Nomes Comerciais & Sinônimos:**")
                    if synonyms:
                        st.caption(", ".join(synonyms))
                    else:
                        st.caption("Sem sinônimos registrados")

            with col_side:
                st.markdown("**Garantia Nutricional Típica:**")
                if isinstance(nutrients, dict) and nutrients:
                    for nut, val in nutrients.items():
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: space-between; background-color: #F8FAF9; border: 1px solid #E5EAE7; border-radius: 6px; padding: 0.35rem 0.65rem; margin-bottom: 0.35rem;">
                                <span style="font-weight: 600; color: #1B4332;">{nut}</span>
                                <span style="font-weight: 700; color: #2D6A4F;">{val}%</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("Não declarada")

                st.write("")
                if st.button("🔍 Ver Ficha Técnica", key=f"btn_modal_{idx}_{fert_dict.get('id', idx)}", use_container_width=True):
                    show_fertilizer_details_modal(fert_dict)

    render_source_badge("Catálogo Mapeado FertiPartner", "Cadastro Homologado")


if __name__ == "__main__":
    render_page()

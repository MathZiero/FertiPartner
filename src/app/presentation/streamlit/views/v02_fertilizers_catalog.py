"""Catálogo de Fertilizantes e Especificações Técnicas."""

import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
    show_fertilizer_details_modal,
)


def render_view() -> None:
    render_header(
        title="Catálogo de Fertilizantes",
        subtitle="Especificações e garantias nutricionais dos fertilizantes homologados. Acesse a ficha técnica completa para detalhes fiscais e laboratoriais.",
        badge_text="Catálogo Oficial",
        badge_type="emerald",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()

    if df_fert.empty:
        st.warning("Nenhum fertilizante cadastrado no catálogo.")
        return

    # Lista de categorias disponíveis
    raw_categories = sorted(df_fert["category_name"].dropna().unique().tolist())
    if not raw_categories:
        st.warning("Nenhuma categoria identificada.")
        return

    selected_cat = st.segmented_control(
        "Selecione a Categoria de Fertilizantes:",
        raw_categories,
        default=raw_categories[0],
        key="p02_cat_filter",
    )
    if not selected_cat:
        selected_cat = raw_categories[0]

    filtered_df = df_fert[df_fert["category_name"] == selected_cat].copy()

    st.divider()
    st.markdown(f"#### 📦 Fertilizantes em *{selected_cat}* ({len(filtered_df)} itens)")

    if filtered_df.empty:
        st.info("Nenhum produto cadastrado nesta categoria.")
        return

    # Exibição simplificada e limpa: Nome, Descrição, Garantia Nutricional e Botão Ficha Técnica
    for idx, row in filtered_df.iterrows():
        fert_dict = row.to_dict()
        canonical_name = fert_dict.get("canonical_name", "Fertilizante")
        description = fert_dict.get("description", "Sem descrição disponível.")
        nutrients = fert_dict.get("typical_nutrients") or {}

        with st.container(border=True):
            col_main, col_side = st.columns([7, 5])

            with col_main:
                st.markdown(f"<h3 style='margin-top: 0; color: #1B4332; font-size: 1.35rem;'>{canonical_name}</h3>", unsafe_allow_html=True)
                st.markdown(description)

            with col_side:
                st.markdown("**Garantia Nutricional:**")
                if isinstance(nutrients, dict) and nutrients:
                    nut_items = []
                    for nut, val in nutrients.items():
                        nut_items.append(
                            f"<div style='display: flex; justify-content: space-between; background-color: #F8FAF9; border: 1px solid #E5EAE7; border-radius: 6px; padding: 0.3rem 0.6rem; margin-bottom: 0.3rem;'>"
                            f"<span style='font-weight: 600; color: #1B4332;'>{nut}</span>"
                            f"<span style='font-weight: 700; color: #2D6A4F;'>{val}%</span>"
                            f"</div>"
                        )
                    st.markdown("".join(nut_items), unsafe_allow_html=True)
                else:
                    st.caption("Garantia nutricional não declarada")

                st.write("")
                if st.button("📋 Ficha Técnica", key=f"btn_modal_{idx}_{fert_dict.get('id', idx)}", use_container_width=True):
                    show_fertilizer_details_modal(fert_dict)

    st.divider()
    render_source_badge("Catálogo Mapeado FertiPartner", "Cadastro Homologado")


if __name__ == "__main__":
    render_view()

"""Catálogo de Fertilizantes e Especificações Técnicas."""

import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_source_badge,
    show_fertilizer_details_modal,
    render_units_legend,
)


def render_view() -> None:
    render_header(
        title="Catálogo de Fertilizantes",
        subtitle="Especificações agronômicas, laboratoriais e garantias nutricionais dos fertilizantes homologados.",
        badge_text="Catálogo Oficial",
        badge_type="emerald",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()

    if df_fert.empty:
        st.warning("Nenhum fertilizante cadastrado no catálogo.")
        return

    # Ordem lógica preferencial das categorias de fertilizantes (inclui secundários e micronutrientes)
    preferred_order = [
        "Fertilizantes Nitrogenados",
        "Fertilizantes Fosfatados",
        "Fertilizantes Potássicos",
        "Macronutrientes Secundários",
        "Misturas e Complexos NPK",
        "Micronutrientes",
    ]
    all_cats = sorted(df_fert["category_name"].dropna().unique().tolist())
    ordered_cats = [c for c in preferred_order if c in all_cats] + [c for c in all_cats if c not in preferred_order]

    category_icons = {
        "Fertilizantes Nitrogenados": "🌱",
        "Fertilizantes Fosfatados": "🌾",
        "Fertilizantes Potássicos": "🌿",
        "Macronutrientes Secundários": "🟡",
        "Misturas e Complexos NPK": "🧪",
        "Micronutrientes": "🔬",
    }

    cols_per_row = 3

    for cat_idx, category in enumerate(ordered_cats):
        cat_df = df_fert[df_fert["category_name"] == category].copy()
        if cat_df.empty:
            continue

        icon = category_icons.get(category, "📦")
        st.markdown(f"### {icon} {category} ({len(cat_df)} produtos)")

        records = cat_df.to_dict("records")
        for i in range(0, len(records), cols_per_row):
            batch = records[i : i + cols_per_row]
            cols = st.columns(cols_per_row)

            for col_idx, fert_dict in enumerate(batch):
                with cols[col_idx]:
                    canonical_name = fert_dict.get("canonical_name", "Fertilizante")
                    description = fert_dict.get("description", "Sem descrição cadastrada.")
                    nutrients = fert_dict.get("typical_nutrients") or {}
                    chem = fert_dict.get("chemical_formula")
                    fert_id = fert_dict.get("id", f"{cat_idx}_{i}_{col_idx}")

                    with st.container(border=True):
                        # Nome do fertilizante
                        st.markdown(
                            f"<div style='min-height: 2.8rem; display: flex; align-items: center;'>"
                            f"<h4 style='margin: 0; color: #1B4332; font-size: 1.15rem; font-weight: 700; line-height: 1.3;'>{canonical_name}</h4>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        # Fórmula química quando existente
                        if chem:
                            st.markdown(
                                f"<div style='margin-bottom: 0.4rem;'>"
                                f"<span style='background-color: #E8F5E9; color: #2D6A4F; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid #C8E6C9;'>{chem}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)

                        # Descrição com alinhamento visual
                        st.markdown(
                            f"<p style='color: #4B5563; font-size: 0.88rem; margin: 0.4rem 0 0.8rem 0; min-height: 3.4rem; line-height: 1.4;'>"
                            f"{description}"
                            f"</p>",
                            unsafe_allow_html=True,
                        )

                        # Garantia Nutricional em Badges
                        st.markdown("<p style='font-size: 0.82rem; font-weight: 600; color: #1B4332; margin-bottom: 0.3rem;'>Garantia Nutricional:</p>", unsafe_allow_html=True)
                        if isinstance(nutrients, dict) and nutrients:
                            nut_badges = []
                            for nut, val in nutrients.items():
                                nut_badges.append(
                                    f"<span style='display: inline-block; background-color: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; font-weight: 600; font-size: 0.82rem; padding: 0.2rem 0.55rem; border-radius: 6px; margin-right: 0.3rem; margin-bottom: 0.3rem;'>"
                                    f"<strong>{nut}:</strong> {val}%"
                                    f"</span>"
                                )
                            st.markdown(f"<div style='min-height: 2.2rem;'>{''.join(nut_badges)}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='min-height: 2.2rem;'><span style='color: #9CA3AF; font-size: 0.82rem;'>Não declarada</span></div>", unsafe_allow_html=True)

                        st.write("")
                        # Botão da Ficha Técnica no card
                        btn_key = f"btn_card_ficha_{fert_id}"
                        if st.button("📋 Ficha Técnica", key=btn_key, use_container_width=True):
                            show_fertilizer_details_modal(fert_dict)

        st.divider()

    render_units_legend()
    render_source_badge("Catálogo Mapeado FertiPartner", "Cadastro Homologado")


if __name__ == "__main__":
    render_view()

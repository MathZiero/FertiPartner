"""Catálogo de Fertilizantes: Hub Central da Aplicação FertiPartner.

Organizado em categorias agronômicas:
1. Macronutrientes Primários (Nitrogenados, Fosfatados e Potássicos)
2. Macronutrientes Secundários (Enxofre, Cálcio e Magnésio)
3. Micronutrientes (Zinco, Boro, Cobre, Manganês, Molibdênio e Cobalto)
"""

from pathlib import Path
from typing import Any
import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    show_fertilizer_details_modal,
    render_units_legend,
)

_PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"


def _classify_macro_category(cat_name: str) -> str:
    """Classifica as categorias canônicas nas macrocategorias da aplicação."""
    cat_lower = cat_name.lower()
    if any(k in cat_lower for k in ["nitrogenad", "fosfatad", "potássic", "npk"]):
        return "🌱 Macronutrientes Primários"
    if any(k in cat_lower for k in ["secundár", "enxofre"]):
        return "🌿 Macronutrientes Secundários"
    if "micronutriente" in cat_lower:
        return "🔬 Micronutrientes"
    return "🌱 Macronutrientes Primários"


def _classify_primary_subgroup(cat_name: str) -> str:
    """Subdivide macronutrientes primários em Nitrogenados, Fosfatados e Potássicos."""
    cat_lower = cat_name.lower()
    if "nitrogenad" in cat_lower:
        return "Nitrogenados"
    if "fosfatad" in cat_lower:
        return "Fosfatados"
    if "potássic" in cat_lower:
        return "Potássicos"
    return "Nitrogenados"


def _render_fertilizer_cards(records: list[dict[str, Any]], cols_per_row: int = 3) -> None:
    """Renderiza a grade de cards de fertilizantes de forma padronizada."""
    for i in range(0, len(records), cols_per_row):
        batch = records[i : i + cols_per_row]
        cols = st.columns(cols_per_row)

        for col_idx, fert_dict in enumerate(batch):
            with cols[col_idx]:
                canonical_name = fert_dict.get("canonical_name", "Fertilizante")
                slug = fert_dict.get("slug", "ureia")
                description = fert_dict.get("description", "Sem descrição cadastrada.")
                nutrients = fert_dict.get("typical_nutrients") or {}
                chem = fert_dict.get("chemical_formula")
                fert_id = fert_dict.get("id", f"{i}_{col_idx}")

                with st.container(border=True):
                    st.markdown(
                        f"<div style='min-height: 2.8rem; display: flex; align-items: center;'>"
                        f"<h4 style='margin: 0; color: #1B4332; font-size: 1.12rem; font-weight: 700; line-height: 1.3;'>{canonical_name}</h4>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    if chem:
                        st.markdown(
                            f"<div style='margin-bottom: 0.4rem;'>"
                            f"<span style='background-color: #E8F5E9; color: #2D6A4F; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid #C8E6C9;'>{chem}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)

                    st.markdown(
                        f"<p style='color: #4B5563; font-size: 0.86rem; margin: 0.4rem 0 0.8rem 0; min-height: 3.2rem; line-height: 1.4;'>"
                        f"{description}"
                        f"</p>",
                        unsafe_allow_html=True,
                    )

                    st.markdown("<p style='font-size: 0.80rem; font-weight: 600; color: #1B4332; margin-bottom: 0.3rem;'>Garantia Nutricional:</p>", unsafe_allow_html=True)
                    if isinstance(nutrients, dict) and nutrients:
                        nut_badges = [
                            f"<span style='display: inline-block; background-color: #F0FDF4; border: 1px solid #BBF7D0; color: #166534; font-weight: 600; font-size: 0.80rem; padding: 0.15rem 0.5rem; border-radius: 6px; margin-right: 0.25rem; margin-bottom: 0.25rem;'>"
                            f"<strong>{nut}:</strong> {val}%</span>"
                            for nut, val in nutrients.items()
                        ]
                        st.markdown(f"<div style='min-height: 2.2rem;'>{''.join(nut_badges)}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='min-height: 2.2rem;'><span style='color: #9CA3AF; font-size: 0.80rem;'>Não declarada</span></div>", unsafe_allow_html=True)

                    st.write("")
                    # Link direto para a página individual do fertilizante
                    page_file = str(_PAGES_DIR / f"fert_{slug.replace('-', '_')}.py")
                    try:
                        st.page_link(page_file, label="📊 Acessar Painel do Produto", width="stretch")
                    except Exception:
                        st.caption(f"Acesse '{canonical_name}' na sidebar.")

                    # Botão da Ficha Técnica modal
                    if st.button("📋 Ficha Técnica Rápida", key=f"btn_modal_{fert_id}", width="stretch"):
                        show_fertilizer_details_modal(fert_dict)


def render_view() -> None:
    render_header(
        title="Catálogo Central de Fertilizantes",
        subtitle="Núcleo estratégico de insumos: especificações agronômicas, garantias nutricionais e acesso direto às páginas dedicadas de cada fertilizante.",
        badge_text="Hub Central",
        badge_type="emerald",
    )

    df_fert = FertiDataService.get_fertilizer_profiles()

    if df_fert.empty:
        st.warning("Nenhum fertilizante cadastrado no catálogo.")
        return

    # Contadores agronômicos detalhados
    n_count = sum(1 for _, r in df_fert.iterrows() if _classify_primary_subgroup(r.get("category_name", "")) == "Nitrogenados" and _classify_macro_category(r.get("category_name", "")) == "🌱 Macronutrientes Primários")
    p_count = sum(1 for _, r in df_fert.iterrows() if _classify_primary_subgroup(r.get("category_name", "")) == "Fosfatados" and _classify_macro_category(r.get("category_name", "")) == "🌱 Macronutrientes Primários")
    k_count = sum(1 for _, r in df_fert.iterrows() if _classify_primary_subgroup(r.get("category_name", "")) == "Potássicos" and _classify_macro_category(r.get("category_name", "")) == "🌱 Macronutrientes Primários")
    sec_count = sum(1 for _, r in df_fert.iterrows() if _classify_macro_category(r.get("category_name", "")) == "🌿 Macronutrientes Secundários")
    micro_count = 6

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card(
            title="Nitrogenados (N)",
            value=f"{n_count} Produtos",
            delta="Ureia, Amônia, Nitratos",
            delta_positive=True,
            help_text="Fontes nitrogenadas de alta concentração",
        )
    with k2:
        render_kpi_card(
            title="Fosfatados (P)",
            value=f"{p_count} Produtos",
            delta="MAP, DAP, Superfosfatos",
            delta_positive=True,
            help_text="Fontes de fósforo para adubação de plantio",
        )
    with k3:
        render_kpi_card(
            title="Potássicos (K)",
            value=f"{k_count} Produtos",
            delta="KCl, SOP",
            delta_positive=True,
            help_text="Fontes de potássio para osmorregulação e grãos",
        )
    with k4:
        render_kpi_card(
            title="Secundários (S)",
            value=f"{sec_count} Produto",
            delta="Enxofre Elementar",
            delta_positive=True,
            help_text="Macronutrientes secundários essenciais",
        )
    with k5:
        render_kpi_card(
            title="Micronutrientes",
            value=f"{micro_count} Elementos",
            delta="Zn, B, Cu, Mn, Mo, Co",
            delta_positive=True,
            help_text="Insumos de precisão em doses reduzidas",
        )

    st.divider()

    # ==============================================================================
    # 1. MACRONUTRIENTES PRIMÁRIOS (COM SUBDIVISÃO NITROGENADOS, FOSFATADOS E POTÁSSICOS)
    # ==============================================================================
    st.markdown("## 🌱 Macronutrientes Primários")
    st.caption("Fertilizantes de maior volume e valor da pauta agrícola global, essenciais na adubação de base e cobertura.")

    prim_df = df_fert[df_fert["category_name"].apply(_classify_macro_category) == "🌱 Macronutrientes Primários"]

    subgroups = [
        ("Nitrogenados", "🔹 Fertilizantes Nitrogenados (N)", "Fontes de nitrogênio para desenvolvimento vegetativo, síntese proteica e biomassa."),
        ("Fosfatados", "🔸 Fertilizantes Fosfatados (P)", "Insumos concentrados em fósforo solúvel e total para enraizamento e arranque inicial das culturas."),
        ("Potássicos", "🟣 Fertilizantes Potássicos (K)", "Fontes de potássio fundamentais para osmorregulação vegetal, enchimento de grãos e tolerância a estresses."),
    ]

    for sub_key, sub_title, sub_desc in subgroups:
        st.markdown(f"#### {sub_title}")
        st.caption(sub_desc)
        subset_df = prim_df[prim_df["category_name"].apply(_classify_primary_subgroup) == sub_key]
        if not subset_df.empty:
            _render_fertilizer_cards(subset_df.to_dict("records"))
        else:
            st.info(f"Nenhum produto cadastrado no grupo de {sub_key}.")
        st.write("")

    st.divider()

    # ==============================================================================
    # 2. MACRONUTRIENTES SECUNDÁRIOS
    # ==============================================================================
    st.markdown("## 🌿 Macronutrientes Secundários")
    st.caption("Insumos fornecedores de Enxofre (S), Cálcio (Ca) e Magnésio (Mg) para o equilíbrio químico e estrutural das plantas.")

    sec_df = df_fert[df_fert["category_name"].apply(_classify_macro_category) == "🌿 Macronutrientes Secundários"]
    if not sec_df.empty:
        _render_fertilizer_cards(sec_df.to_dict("records"))
    else:
        st.info("Nenhum produto cadastrado nesta categoria.")

    st.divider()

    # ==============================================================================
    # 3. MICRONUTRIENTES
    # ==============================================================================
    st.markdown("## 🔬 Micronutrientes")
    st.caption("Nutrientes vitais para a fisiologia vegetal aplicados em frações menores: Zinco (Zn), Boro (B), Cobre (Cu), Manganês (Mn), Molibdênio (Mo) e Cobalto (Co).")

    with st.container(border=True):
        c_txt, c_btn = st.columns([8, 4])
        with c_txt:
            st.markdown("#### 🔬 Painel Estratégico de Micronutrientes")
            st.write("Acesse o painel completo de demanda, balanço de fornecimento e dependência externa de Zinco, Boro, Cobre, Manganês, Molibdênio e Cobalto no agronegócio nacional.")
        with c_btn:
            st.write("")
            try:
                st.page_link(str(_PAGES_DIR / "fert_micronutrientes.py"), label="👉 Abrir Painel de Micronutrientes", icon=":material/biotech:", width="stretch")
            except Exception:
                st.info("Acesse 'Micronutrientes' na barra lateral.")

    st.divider()

    render_units_legend()
    render_source_badge("Catálogo Mapeado FertiPartner", "Cadastro Homologado")


def render_page() -> None:
    render_view()


if __name__ == "__main__":
    render_page()

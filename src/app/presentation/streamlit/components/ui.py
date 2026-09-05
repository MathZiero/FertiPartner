"""Componentes visuais nativos e reutilizáveis para as páginas do FertiPartner (Light Mode)."""

from typing import Any
import pandas as pd
import streamlit as st


def render_header(
    title: str,
    subtitle: str | None = None,
    badge_text: str | None = None,
    badge_type: str = "emerald",
) -> None:
    """Renderiza um cabeçalho limpo, moderno e perfeitamente centralizado para as páginas."""
    badge_html = ""
    if badge_text:
        badge_color = {
            "emerald": "#2D6A4F",
            "blue": "#1D4ED8",
            "purple": "#6D28D9",
            "amber": "#B45309",
        }.get(badge_type, "#2D6A4F")
        badge_bg = {
            "emerald": "#D8F3DC",
            "blue": "#DBEAFE",
            "purple": "#EDE9FE",
            "amber": "#FEF3C7",
        }.get(badge_type, "#D8F3DC")
        badge_html = (
            f'<div style="text-align: center; margin-bottom: 0.5rem;">'
            f'<span style="display: inline-block; padding: 0.25rem 0.85rem; border-radius: 9999px; '
            f'background-color: {badge_bg}; color: {badge_color}; font-size: 0.78rem; '
            f'font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">'
            f'{badge_text}</span></div>'
        )

    subtitle_html = (
        f'<p style="text-align: center; color: #4B5563; font-size: 1.02rem; '
        f'margin-top: 0.45rem; margin-bottom: 0; max-width: 820px; margin-left: auto; '
        f'margin-right: auto; line-height: 1.5;">{subtitle}</p>'
        if subtitle else ""
    )

    st.markdown(
        f"""
        <div class="fp-header-container">
            {badge_html}
            <h1 class="fp-header-title" style="text-align: center !important; font-size: 2.2rem; font-weight: 800; color: #1B4332; margin: 0; letter-spacing: -0.02em;">
                {title}
            </h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    title: str,
    value: str,
    delta: str | None = None,
    delta_positive: bool | None = None,
    help_text: str | None = None,
) -> None:
    """Renderiza um indicador de desempenho (KPI) utilizando st.metric nativo em container com borda."""
    with st.container(border=True):
        if delta_positive is True:
            delta_color = "normal"
        elif delta_positive is False:
            delta_color = "inverse"
        else:
            delta_color = "off" if delta is None else "normal"

        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color,
            help=help_text,
        )


def render_source_badge(source_name: str, frequency: str = "Mensal") -> None:
    """Exibe badge informativa de rastreabilidade da fonte e frequência de atualização."""
    st.caption(f"ℹ️ **Fonte:** {source_name} • **Frequência:** {frequency} • **Status:** Oficial / Homologado")


@st.dialog("Ficha Técnica do Fertilizante")
def show_fertilizer_details_modal(fert: dict[str, Any]) -> None:
    """Abre um modal nativo moderno (st.dialog) com especificações técnicas e agronômicas."""
    st.subheader(f"{fert.get('canonical_name', 'Fertilizante')}")
    st.caption(f"Categoria: {fert.get('category_name', 'N/A')} | Fórmula Química: `{fert.get('chemical_formula', 'N/A')}`")

    st.write(f"**Descrição e Aplicação Agrícola:** {fert.get('description', 'Sem descrição cadastrada.')}")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**Identificação:**")
            st.markdown(f"- **CAS RN:** `{fert.get('cas_rn', 'N/A')}`")
            st.markdown(f"- **Código Interno:** `{fert.get('slug', 'N/A')}`")

    with c2:
        with st.container(border=True):
            st.markdown("**Garantia Nutricional Típica:**")
            nutrients = fert.get("typical_nutrients") or {}
            if isinstance(nutrients, dict) and nutrients:
                for nut, val in nutrients.items():
                    st.markdown(f"- **{nut}:** `{val}%`")
            else:
                st.write("Garantias nutricionais não declaradas.")

    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("**Classificações Fiscais e Aduaneiras (NCM / HS):**")
            codes = fert.get("hs_ncm_codes") or []
            if codes:
                st.markdown(" ".join([f"`{c}`" for c in codes]))
            else:
                st.write("Nenhum código aduaneiro associado.")

    with c4:
        with st.container(border=True):
            st.markdown("**Sinônimos Comerciais:**")
            synonyms = fert.get("synonyms") or []
            if synonyms:
                st.markdown(", ".join(synonyms))
            else:
                st.write("Nenhum sinônimo comercial cadastrado.")


def render_download_csv_button(
    df: pd.DataFrame,
    filename: str = "fertipartner_data.csv",
    label: str = "Baixar Tabela (CSV)",
    key: str | None = None,
) -> None:
    """Função mantida para retrocompatibilidade, sem renderizar botões de download."""
    pass

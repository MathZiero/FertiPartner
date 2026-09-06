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


@st.dialog("Ficha Técnica do Fertilizante", width="large")
def show_fertilizer_details_modal(fert: dict[str, Any]) -> None:
    """Abre um modal nativo moderno (st.dialog) com especificações agronômicas, laboratoriais e fiscais completas."""
    canonical_name = fert.get("canonical_name", "Fertilizante")
    category = fert.get("category_name", "N/A")
    chem_formula = fert.get("chemical_formula", "N/A")
    cas_rn = fert.get("cas_rn", "N/A")
    slug = fert.get("slug", "N/A")

    st.markdown(f"### {canonical_name}")
    st.caption(f"🏷️ **Categoria:** {category} | 🧪 **Fórmula Química:** `{chem_formula}` | 🔢 **CAS RN:** `{cas_rn}`")

    # Abas organizadas de especificações
    tab_agro, tab_chem, tab_storage, tab_customs = st.tabs([
        "🌱 Aplicação Agronômica",
        "🔬 Propriedades Físico-Químicas",
        "📦 Armazenagem & Manuseio",
        "📑 Fiscal & Aduaneiro",
    ])

    with tab_agro:
        st.markdown("**Descrição Geral do Insumo:**")
        st.write(fert.get("detailed_description") or fert.get("description", "Sem descrição cadastrada."))

        st.markdown("**Aplicação Agronômica & Dinâmica no Solo:**")
        st.info(fert.get("agronomic_usage") or "Aplicação agronômica de acordo com recomendação de análise de solo e engenheiro agrônomo responsável.")

    with tab_chem:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("**Garantia Nutricional Típica (% em peso / p/p):**")
                nutrients = fert.get("typical_nutrients") or {}
                if isinstance(nutrients, dict) and nutrients:
                    for nut, val in nutrients.items():
                        st.markdown(f"- **{nut}:** `{val}%`")
                else:
                    st.write("Garantias nutricionais não declaradas.")

        with c2:
            with st.container(border=True):
                st.markdown("**Propriedades Físicas & Aspecto:**")
                st.write(fert.get("physical_properties") or "Grânulos sólidos uniformes com alta fluidez mecânica para dosadores.")

    with tab_storage:
        with st.container(border=True):
            st.markdown("**Recomendações de Armazenamento & Manuseio Seguro:**")
            st.write(fert.get("handling_storage") or "Armazenar em local seco, coberto, arejado e sobre estrados de madeira protegidos de umidade excessiva.")

    with tab_customs:
        c_ncm, c_syn = st.columns(2)
        with c_ncm:
            with st.container(border=True):
                st.markdown("**Classificações Fiscais (NCM / HS Code):**")
                codes = fert.get("hs_ncm_codes") or []
                if codes:
                    st.markdown(" ".join([f"`{c}`" for c in codes]))
                else:
                    st.write("Nenhum código aduaneiro associado.")
                st.caption("NCM (8 dígitos Mercosul / Brasil) • HS Code (6 dígitos Sistema Harmonizado)")

        with c_syn:
            with st.container(border=True):
                st.markdown("**Sinônimos Comerciais & Internacionais:**")
                synonyms = fert.get("synonyms") or []
                if synonyms:
                    st.markdown(", ".join(synonyms))
                else:
                    st.write("Nenhum sinônimo cadastrado.")
                st.markdown(f"**Identificador Interno (Slug):** `{slug}`")


def render_units_legend() -> None:
    """Renderiza legenda explicativa das unidades de medida físicas, agronômicas e termos aduaneiros utilizados."""
    with st.expander("ℹ️ Legenda de Unidades de Medida e Termos Aduaneiros Utilizados", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            **Unidades Físicas, Agronômicas e Financeiras:**
            - **MT ou t:** Toneladas Métricas ($1.000\\text{ kg}$ ou $1\\text{ milhão de gramas}$).
            - **k MT:** Milhares de Toneladas Métricas ($1.000\\text{ MT} = 1.000.000\\text{ kg}$).
            - **M MT (ou Mi t):** Milhões de Toneladas Métricas ($1.000.000\\text{ MT}$).
            - **kg ou g/ha:** Quilogramas ou Gramas por hectare (usados em micronutrientes e corretivos).
            - **USD/MT (ou $/t):** Dólares Americanos por Tonelada Métrica de produto físico.
            - **% p/p (Garantia Nutricional):** Porcentagem em massa do nutriente garantido no fertilizante (ex.: Ureia $46\\%\\text{ N}$).
            """)
        with c2:
            st.markdown("""
            **Incoterms Comerciais e Classificações Aduaneiras:**
            - **FOB (Free On Board):** Preço da mercadoria entregue a bordo do navio no porto de origem/embarque (não inclui frete marítimo internacional).
            - **CFR (Cost and Freight):** Preço da mercadoria com frete marítimo internacional incluso até o porto de desembarque no Brasil.
            - **NCM (8 dígitos):** Nomenclatura Comum do Mercosul (classificação fiscal oficial brasileira utilizada pela Receita Federal e MDIC).
            - **HS Code (6 dígitos):** Sistema Harmonizado da Organização Mundial das Alfândegas (utilizado na ONU Comtrade).
            - **CAS RN:** Chemical Abstracts Service Registry Number (identificador químico global único).
            """)


def render_download_csv_button(
    df: pd.DataFrame,
    filename: str = "fertipartner_data.csv",
    label: str = "Baixar Tabela (CSV)",
    key: str | None = None,
) -> None:
    """Função mantida para retrocompatibilidade, sem renderizar botões de download."""
    pass

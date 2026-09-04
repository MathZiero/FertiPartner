"""Componentes visuais nativos e reutilizáveis para as páginas do FertiPartner."""

from typing import Any
import pandas as pd
import streamlit as st


def render_header(
    title: str,
    subtitle: str | None = None,
    badge_text: str | None = None,
    badge_type: str = "emerald",
) -> None:
    """Renderiza um cabeçalho limpo e moderno utilizando componentes nativos do Streamlit."""
    col_title, col_badge = st.columns([10, 2])
    with col_title:
        st.title(title)
        if subtitle:
            st.caption(subtitle)
    with col_badge:
        if badge_text:
            badge_color = {
                "emerald": "green",
                "blue": "blue",
                "purple": "violet",
                "amber": "orange",
            }.get(badge_type, "green")
            st.markdown(f":{badge_color}-background[**{badge_text}**]")

    st.divider()


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
    """Exibe badge informativa de rastreabilidade da fonte e frequência de atualização (RF17)."""
    st.caption(f"ℹ️ **Fonte:** {source_name} • **Frequência:** {frequency} • **Padrão:** 4NF / ISO")


@st.dialog("Ficha Técnica do Fertilizante")
def show_fertilizer_details_modal(fert: dict[str, Any]) -> None:
    """Abre um modal nativo moderno (st.dialog) com especificações técnicas e químicas."""
    st.subheader(f"{fert.get('canonical_name', 'Fertilizante')}")
    st.caption(f"Categoria: {fert.get('category_name', 'N/A')} | Fórmula: `{fert.get('chemical_formula', 'N/A')}`")

    st.write(f"**Descrição:** {fert.get('description', 'Sem descrição cadastrada.')}")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("**Identificação Química:**")
            st.markdown(f"- **CAS RN:** `{fert.get('cas_rn', 'N/A')}`")
            st.markdown(f"- **Slug do Sistema:** `{fert.get('slug', 'N/A')}`")

    with c2:
        with st.container(border=True):
            st.markdown("**Composição Nutricional Típica:**")
            nutrients = fert.get("typical_nutrients") or {}
            if isinstance(nutrients, dict) and nutrients:
                for nut, val in nutrients.items():
                    st.markdown(f"- **{nut}:** `{val}%`")
            else:
                st.write("Dados nutricionais não disponíveis.")

    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.markdown("**Classificações Fiscais (HS / NCM):**")
            codes = fert.get("hs_ncm_codes") or []
            if codes:
                st.markdown(" ".join([f"`{c}`" for c in codes]))
            else:
                st.write("Nenhum código cadastrado.")

    with c4:
        with st.container(border=True):
            st.markdown("**Sinônimos Comerciais:**")
            synonyms = fert.get("synonyms") or []
            if synonyms:
                st.markdown(", ".join(synonyms))
            else:
                st.write("Nenhum sinônimo.")


def render_download_csv_button(
    df: pd.DataFrame,
    filename: str = "fertipartner_data.csv",
    label: str = "Baixar Tabela (CSV)",
    key: str | None = None,
) -> None:
    """Renderiza botão estilizado nativo para exportar DataFrame para CSV."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 {label}",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        key=key,
    )

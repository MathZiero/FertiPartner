"""Componentes visuais reutilizáveis para as páginas do FertiPartner."""

from typing import Any
import pandas as pd
import streamlit as st


def render_header(
    title: str,
    subtitle: str | None = None,
    badge_text: str | None = None,
    badge_type: str = "emerald",
) -> None:
    """Renderiza um cabeçalho moderno e impactante com estética AgTech."""
    badge_html = ""
    if badge_text:
        badge_html = f'<span class="fp-badge fp-badge-{badge_type}" style="margin-left: 12px; vertical-align: middle;">{badge_text}</span>'

    st.markdown(
        f"""
        <div class="fp-header-container">
            <h1 class="fp-header-title">{title} {badge_html}</h1>
            {f'<p class="fp-header-subtitle">{subtitle}</p>' if subtitle else ''}
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
    """Renderiza um card de indicador de desempenho (KPI) de alto impacto visual."""
    delta_html = ""
    if delta:
        if delta_positive is True:
            delta_class = "fp-delta-positive"
            arrow = "▲"
        elif delta_positive is False:
            delta_class = "fp-delta-negative"
            arrow = "▼"
        else:
            delta_class = "fp-delta-neutral"
            arrow = "•"
        delta_html = f'<span class="{delta_class}">{arrow} {delta}</span>'

    help_html = f'<span style="color: #64748B; font-size: 0.75rem;">{help_text}</span>' if help_text else ""

    st.markdown(
        f"""
        <div class="fp-kpi-card">
            <div class="fp-kpi-title">{title}</div>
            <div class="fp-kpi-value">{value}</div>
            <div class="fp-kpi-footer">
                {delta_html}
                {help_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_badge(source_name: str, frequency: str = "Mensal") -> None:
    """Exibe badge com rastreabilidade da fonte e frequência de atualização (RF17)."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: #94A3B8; margin-top: 10px; margin-bottom: 10px;">
            <span>ℹ️ <b>Fonte:</b> {source_name}</span>
            <span class="fp-badge fp-badge-blue">{frequency}</span>
            <span style="color: #64748B;">• Padrão 4NF / ISO</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Ficha Técnica do Fertilizante")
def show_fertilizer_details_modal(fert: dict[str, Any]) -> None:
    """Abre um modal nativo moderno (st.dialog) com especificações técnicas e químicas."""
    st.subheader(f"{fert.get('canonical_name', 'Fertilizante')}")
    st.caption(f"Categoria: {fert.get('category_name', 'N/A')} | Fórmula: `{fert.get('chemical_formula', 'N/A')}`")

    st.markdown(f"**Descrição:** {fert.get('description', 'Sem descrição cadastrada.')}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Identificação Química:**")
        st.markdown(f"- **CAS RN:** `{fert.get('cas_rn', 'N/A')}`")
        st.markdown(f"- **Slug do Sistema:** `{fert.get('slug', 'N/A')}`")

    with c2:
        st.markdown("**Composição Nutricional Típica:**")
        nutrients = fert.get("typical_nutrients") or {}
        if isinstance(nutrients, dict) and nutrients:
            for nut, val in nutrients.items():
                st.markdown(f"- **{nut}:** `{val}%`")
        else:
            st.write("Dados nutricionais não disponíveis.")

    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Classificações Fiscais (HS / NCM):**")
        codes = fert.get("hs_ncm_codes") or []
        if codes:
            st.markdown(" ".join([f"`{c}`" for c in codes]))
        else:
            st.write("Nenhum código cadastrado.")

    with c4:
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
) -> None:
    """Renderiza botão estilizado para exportar DataFrame para CSV."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 {label}",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )

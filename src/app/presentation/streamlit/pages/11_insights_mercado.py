"""Página 11: Sistema de Insights e Alertas Automáticos de Mercado (RF23)."""

import sys
import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    render_download_csv_button,
)


def render_page() -> None:
    render_header(
        title="Insights & Alertas Automáticos de Mercado",
        subtitle="Motor analítico determinístico para detecção de anomalias de preço, alertas de dependência crítica e janelas de compra do agronegócio.",
        badge_text="RF23 Insights",
        badge_type="purple",
    )

    # Obtenção dos insights gerados pelo motor de aplicação
    insights = FertiDataService.get_market_insights()

    if not insights:
        st.info("Nenhum alerta ou anomalia identificado no momento. O mercado opera dentro das faixas históricas normais.")
        return

    # Métricas gerais
    total_insights = len(insights)
    critical_count = sum(1 for i in insights if i.get("is_critical"))
    price_alerts = sum(1 for i in insights if i.get("category") in ("Volatilidade de Mercado", "Oportunidade de Compra"))
    supply_alerts = sum(1 for i in insights if i.get("category") == "Segurança de Suprimento")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Total de Alertas Gerados",
            value=f"{total_insights} Alertas",
            delta="Varredura Ativa",
            delta_positive=True,
            help_text="Insights gerados pelo motor analítico",
        )
    with c2:
        render_kpi_card(
            title="Alertas Críticos",
            value=f"{critical_count}",
            delta="Ação Recomendada" if critical_count > 0 else "Estável",
            delta_positive=False if critical_count > 0 else True,
            help_text="Exigem atenção imediata de risco",
        )
    with c3:
        render_kpi_card(
            title="Sinais de Preço / Volatilidade",
            value=f"{price_alerts}",
            delta="Variação MoM Atípica",
            delta_positive=None,
            help_text="Oscilações acima do desvio padrão",
        )
    with c4:
        render_kpi_card(
            title="Riscos de Suprimento (Brasil)",
            value=f"{supply_alerts}",
            delta="Dependência > 70%",
            delta_positive=False if supply_alerts > 0 else True,
            help_text="Concentração de importações",
        )

    st.write("")

    # Filtros de categoria e severidade
    categories = ["Todas"] + sorted(list({i.get("category", "") for i in insights if i.get("category")}))
    col_cat, col_sev = st.columns([6, 6])
    with col_cat:
        selected_cat = st.segmented_control("Filtrar por Categoria", categories, default="Todas", key="p11_cat_ctrl")
    with col_sev:
        severities = ["Todas", "CRITICAL", "WARNING", "INFO"]
        selected_sev = st.segmented_control("Filtrar por Severidade", severities, default="Todas", key="p11_sev_ctrl")

    # Filtragem
    filtered_insights = insights
    if selected_cat != "Todas":
        filtered_insights = [i for i in filtered_insights if i.get("category") == selected_cat]
    if selected_sev != "Todas":
        filtered_insights = [i for i in filtered_insights if i.get("severity") == selected_sev]

    st.subheader(f"🔔 Alertas e Oportunidades de Inteligência ({len(filtered_insights)})")

    # Renderização de cada insight
    for item in filtered_insights:
        sev = item.get("severity", "INFO")
        border_color = "#F43F5E" if sev == "CRITICAL" else ("#F59E0B" if sev == "WARNING" else "#3B82F6")
        badge_label = "🚨 CRÍTICO" if sev == "CRITICAL" else ("⚠️ ATENÇÃO" if sev == "WARNING" else "ℹ️ OPORTUNIDADE")

        with st.container(border=True):
            col_header, col_pill = st.columns([10, 2])
            with col_header:
                st.markdown(f"#### {item.get('title')}")
                st.caption(f"Categoria: **{item.get('category')}** | ID: `{item.get('id')}`")
            with col_pill:
                if sev == "CRITICAL":
                    st.error(badge_label)
                elif sev == "WARNING":
                    st.warning(badge_label)
                else:
                    st.info(badge_label)

            st.write(item.get("message"))

            # Métricas e Linha de Base
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.markdown(f"**{item.get('metric_name')}:** `{item.get('metric_value')}`")
            with m_col2:
                st.markdown(f"**Referência / Limiar:** `{item.get('baseline_value')}`")

            st.divider()
            st.markdown(f"**💡 Ação Estratégica Recomendada:** {item.get('recommended_action')}")

    st.write("")
    df_export = pd.DataFrame(filtered_insights)
    if not df_export.empty:
        render_download_csv_button(df_export, filename="insights_mercado_fertipartner.csv", key="dl_p11_insights")

    render_source_badge("Motor de Regras Analíticas FertiPartner • Base 4NF", "Tempo Real")


if __name__ == "__main__":
    render_page()

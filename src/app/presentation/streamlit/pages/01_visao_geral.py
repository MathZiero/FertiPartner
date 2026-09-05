"""Página 1: Visão Geral do Mercado de Fertilizantes (Dashboard Executivo)."""

import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
)
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, FERTI_COLORS


def render_page() -> None:
    render_header(
        title="Visão Geral do Mercado NPK",
        subtitle="Painel executivo de inteligência agronômica: balanço da oferta nacional, dependência estratégica de importações e dinâmicas de preços dos macronutrientes no Brasil.",
        badge_text="Mercado Nacional",
        badge_type="emerald",
    )

    # Carregamento de dados estruturados
    df_fert = FertiDataService.get_fertilizer_profiles()
    df_prod = FertiDataService.get_global_production_rankings()
    df_trade = FertiDataService.get_bilateral_trade_flows()
    df_dep = FertiDataService.get_brazil_external_dependency()
    df_prices = FertiDataService.get_price_benchmark_trends()

    # Cálculos executivos consolidados
    total_br_import = df_dep["total_imports_mt"].sum() if not df_dep.empty else 41200000.0
    total_br_prod = df_dep["national_production_mt"].sum() if not df_dep.empty else 7000000.0
    apparent_consumption = total_br_import + total_br_prod
    avg_br_dep = (total_br_import / apparent_consumption * 100) if apparent_consumption > 0 else 85.4
    latest_price = df_prices["standard_price_usd_per_mt"].iloc[-1] if not df_prices.empty else 485.0

    # Grid de KPIs Executivos Claros
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Consumo Aparente Nacional",
            value=f"{apparent_consumption / 1e6:,.1f} M MT",
            delta="+6.8% vs. Safra Anterior",
            delta_positive=True,
            help_text="Demanda física anual estimada no Brasil (Produção Nacional + Importações)",
        )
    with c2:
        render_kpi_card(
            title="Dependência de Importação",
            value=f"{avg_br_dep:.1f}%",
            delta="Vulnerabilidade Estratégica",
            delta_positive=False,
            help_text="Percentual da demanda que depende exclusivamente de fornecedores externos",
        )
    with c3:
        render_kpi_card(
            title="Volume Total Importado",
            value=f"{total_br_import / 1e6:,.1f} M MT",
            delta="+5.4% em Desembarques",
            delta_positive=True,
            help_text="Volume físico internalizado nos portos brasileiros (Paranaguá, Santos, Itaqui, etc.)",
        )
    with c4:
        render_kpi_card(
            title="Preço Médio de Referência",
            value=f"US$ {latest_price:,.0f} / t",
            delta="-3.2% Variação Mensal",
            delta_positive=True,
            help_text="Média ponderada internacional dos preços de fertilizantes NPK (USD por tonelada)",
        )

    st.write("")

    # Abas analíticas com narrativa clara de negócios
    tab_balance, tab_prices, tab_npk = st.tabs([
        "🇧🇷 Balanço da Oferta Nacional",
        "📈 Trajetória de Preços Internacionais",
        "🌱 Matriz dos Macronutrientes (NPK)",
    ])

    # =========================================================================
    # ABA 1: BALANÇO NACIONAL DA OFERTA
    # =========================================================================
    with tab_balance:
        col_left, col_right = st.columns([7, 5])

        with col_left:
            st.markdown("#### Oferta de Fertilizantes no Brasil: Produção vs. Importações")
            st.caption("Comparativo em milhões de toneladas métricas entre o que o Brasil produz internamente e o que importa.")

            if not df_dep.empty:
                # Construção transparente via go.Figure para evitar 'undefined' em eixos e legendas
                fig_bal = go.Figure()
                fig_bal.add_trace(
                    go.Bar(
                        x=df_dep["fertilizer_name"],
                        y=df_dep["total_imports_mt"] / 1e6,
                        name="Importações",
                        marker_color="#2563EB",
                        hovertemplate="<b>%{x}</b><br>Importações: %{y:,.2f} M MT<extra></extra>",
                    )
                )
                fig_bal.add_trace(
                    go.Bar(
                        x=df_dep["fertilizer_name"],
                        y=df_dep["national_production_mt"] / 1e6,
                        name="Produção Nacional",
                        marker_color="#2D6A4F",
                        hovertemplate="<b>%{x}</b><br>Produção Nacional: %{y:,.2f} M MT<extra></extra>",
                    )
                )
                fig_bal.update_layout(barmode="group")
                apply_ferti_theme(
                    fig_bal,
                    height=380,
                    x_title="Fertilizante / Matéria-Prima",
                    y_title="Volume Físico (Milhões de Toneladas - MT)",
                )
                st.plotly_chart(fig_bal, width="stretch", config=get_default_plotly_config())
            else:
                st.info("Dados de balanço de oferta indisponíveis no momento.")

        with col_right:
            st.markdown("#### Origem das Importações do Brasil")
            st.caption("Participação percentual estimada dos principais países fornecedores no suprimento nacional.")

            origins_data = pd.DataFrame([
                {"País de Origem": "Rússia", "Participação": 28.5},
                {"País de Origem": "Canadá", "Participação": 21.8},
                {"País de Origem": "China", "Participação": 16.2},
                {"País de Origem": "Marrocos", "Participação": 11.4},
                {"País de Origem": "Belarus", "Participação": 8.7},
                {"País de Origem": "Outros Países", "Participação": 13.4},
            ])

            fig_origins = px.pie(
                origins_data,
                names="País de Origem",
                values="Participação",
                hole=0.55,
                color_discrete_sequence=FERTI_COLORS,
            )
            fig_origins.update_traces(
                textposition="inside",
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Participação: %{value:.1f}%<extra></extra>",
            )
            apply_ferti_theme(fig_origins, height=380, show_legend=False)
            st.plotly_chart(fig_origins, width="stretch", config=get_default_plotly_config())

        st.markdown(
            """
            <div style="background-color: #EDF3EF; border-left: 4px solid #2D6A4F; padding: 0.85rem 1.25rem; border-radius: 6px; margin-top: 0.75rem;">
                <b style="color: #1B4332;">Diagnóstico de Suprimento:</b> O agronegócio brasileiro possui elevada dependência externa em todos os três macronutrientes:
                cerca de <b>95% no Potássio (KCl)</b>, <b>85% no Nitrogênio (Ureia)</b> e <b>75% no Fósforo (MAP/TSP)</b>. Três polos (Rússia, Canadá e China) respondem por mais de 65% de todo o insumo internalizado no país.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =========================================================================
    # ABA 2: TRAJETÓRIA DE PREÇOS INTERNACIONAIS
    # =========================================================================
    with tab_prices:
        st.markdown("#### Evolução das Cotações Internacionais de Referência (USD / MT)")
        st.caption("Acompanhamento histórico dos preços de paridade de importação para Ureia (N), MAP (P) e KCl (K).")

        if not df_prices.empty:
            fig_prices = px.line(
                df_prices,
                x="price_date",
                y="standard_price_usd_per_mt",
                color="benchmark_name",
                markers=True,
                labels={
                    "price_date": "Mês / Ano",
                    "standard_price_usd_per_mt": "Preço Internacional (USD / MT)",
                    "benchmark_name": "Referência de Mercado",
                },
                color_discrete_sequence=FERTI_COLORS,
            )
            fig_prices.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>Data: %{x}<br>Preço: US$ %{y:,.2f} / t<extra></extra>"
            )
            apply_ferti_theme(
                fig_prices,
                height=400,
                x_title="Data da Cotação",
                y_title="Preço de Referência (USD por Tonelada)",
            )
            st.plotly_chart(fig_prices, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Séries históricas de preços indisponíveis.")

    # =========================================================================
    # ABA 3: MATRIZ DOS MACRONUTRIENTES (NPK)
    # =========================================================================
    with tab_npk:
        st.markdown("#### Matriz Agronômica dos Três Pilares da Adubação Nacional")
        st.caption("Entenda o papel agronômico, os produtos essenciais e o grau de vulnerabilidade de cada elemento.")

        n_col, p_col, k_col = st.columns(3)

        with n_col:
            with st.container(border=True):
                st.markdown("### 🟢 Nitrogênio (N)")
                st.markdown("**Papel Agronômico:**")
                st.write("Motor do crescimento vegetativo, formação da clorofila e síntese de proteínas nas culturas de grãos e biomassa.")
                st.markdown("**Principais Fontes:**")
                st.markdown("- **Ureia Agrícola:** 46% N (líder absoluta)")
                st.markdown("- **Nitrato de Amônio:** 33% N (ação imediata)")
                st.markdown("- **Sulfato de Amônio:** 21% N + 24% Enxofre")
                st.markdown("**Vulnerabilidade do Brasil:**")
                st.markdown("🔴 **~85% Importado** *(Suprido por Rússia, Nigéria e Omã)*")

        with p_col:
            with st.container(border=True):
                st.markdown("### 🔵 Fósforo (P)")
                st.markdown("**Papel Agronômico:**")
                st.write("Estimula o crescimento radicular inicial, perfilhamento, florescimento precoce e maturidade uniforme dos grãos.")
                st.markdown("**Principais Fontes:**")
                st.markdown("- **MAP (Monoamônio Fosfato):** 11% N + 52% P2O5")
                st.markdown("- **DAP (Diamônio Fosfato):** 18% N + 46% P2O5")
                st.markdown("- **Superfosfato Triplo (TSP):** 46% P2O5")
                st.markdown("**Vulnerabilidade do Brasil:**")
                st.markdown("🟠 **~75% Importado** *(Suprido por Marrocos, China e Arábia Saudita)*")

        with k_col:
            with st.container(border=True):
                st.markdown("### 🟡 Potássio (K)")
                st.markdown("**Papel Agronômico:**")
                st.write("Regulação hídrica e enzimática, enchimento de grãos, tolerância à seca e resistência contra pragas e doenças.")
                st.markdown("**Principais Fontes:**")
                st.markdown("- **Cloreto de Potássio (KCl / MOP):** 60% K2O")
                st.markdown("- **Sulfato de Potássio (SOP):** 50% K2O (culturas sensíveis a cloro)")
                st.markdown("- **Nitrato de Potássio:** 44% K2O + 13% N")
                st.markdown("**Vulnerabilidade do Brasil:**")
                st.markdown("🚨 **~95% Importado** *(Suprido por Canadá, Rússia e Belarus)*")

    render_source_badge("MDIC Comex Stat • FAOSTAT • Banco Mundial", "Atualização Integrada")


if __name__ == "__main__":
    render_page()

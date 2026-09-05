"""Página 10: Sazonalidade das Safras e Ciclos de Demanda Agrícola (RF10)."""

import sys
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    render_download_csv_button,
)
from app.presentation.streamlit.theme import apply_ferti_theme, get_default_plotly_config, FERTI_COLORS


def render_page() -> None:
    render_header(
        title="Sazonalidade das Safras & Ciclos de Demanda",
        subtitle="Mapeamento das janelas de compras agrícolas, índices sazonais mensais (Base 100) e concentração portuária (Safra vs. Safrinha).",
        badge_text="RF10 Sazonalidade",
        badge_type="emerald",
    )

    # Filtro de fertilizante
    df_fert = FertiDataService.get_fertilizer_profiles()
    fert_options = ["Todos"] + (df_fert["canonical_name"].tolist() if not df_fert.empty else ["Ureia", "MAP", "KCl"])
    
    col_filter, col_spacer = st.columns([5, 7])
    with col_filter:
        selected_fert = st.selectbox("Selecione o Segmento:", fert_options, key="p10_fert_select")

    # Obtenção dos dados de sazonalidade
    df_seas = FertiDataService.get_seasonality_patterns(fertilizer_name=selected_fert)

    if df_seas.empty:
        st.warning("Dados sazonais não disponíveis.")
        return

    # Métricas de destaque
    peak_row = df_seas.sort_values(by="seasonality_index", ascending=False).iloc[0]
    low_row = df_seas.sort_values(by="seasonality_index", ascending=True).iloc[0]
    current_month_num = datetime.now().month
    curr_row = df_seas[df_seas["month"] == current_month_num].iloc[0] if not df_seas[df_seas["month"] == current_month_num].empty else df_seas.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Mês de Pico Máximo",
            value=f"{peak_row['month_name']}",
            delta=f"Índice {peak_row['seasonality_index']:.1f}",
            delta_positive=True,
            help_text="Maior concentração anual de importações",
        )
    with c2:
        render_kpi_card(
            title="Mês de Menor Movimento",
            value=f"{low_row['month_name']}",
            delta=f"Índice {low_row['seasonality_index']:.1f}",
            delta_positive=None,
            help_text="Período de menor fluxo portuário",
        )
    with c3:
        render_kpi_card(
            title="Concentração no 3º Trimestre (Q3)",
            value="35.5% do Ano",
            delta="Pico Safra Verão",
            delta_positive=True,
            help_text="Meses de Julho a Setembro",
        )
    with c4:
        render_kpi_card(
            title="Mês Atual no Calendário",
            value=f"{curr_row['month_name']}",
            delta=f"{curr_row['peak_status']}",
            delta_positive=True if curr_row['seasonality_index'] >= 100 else False,
            help_text=f"Fase: {curr_row['crop_calendar_phase']}",
        )

    st.write("")

    tab_curve, tab_crops, tab_table = st.tabs([
        "📈 Curva Sazonal & Índice Base 100",
        "🚜 Calendário Agrícola (Safra vs. Safrinha)",
        "📋 Matriz Numérica Mensal",
    ])

    with tab_curve:
        st.subheader("📊 Distribuição Mensal de Entregas & Índice Sazonal")

        fig = go.Figure()

        # Barras de Volume
        fig.add_trace(
            go.Bar(
                x=df_seas["month_name"],
                y=df_seas["average_volume_mt"],
                name="Volume Médio (MT)",
                marker_color="#3B82F6",
                yaxis="y1",
                hovertemplate="<b>%{x}</b><br>Volume: %{y:,.0f} MT<extra></extra>",
            )
        )

        # Linha de Índice Sazonal
        fig.add_trace(
            go.Scatter(
                x=df_seas["month_name"],
                y=df_seas["seasonality_index"],
                name="Índice Sazonal (Base 100)",
                marker=dict(color="#10B981", size=8),
                line=dict(color="#10B981", width=3),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Índice Sazonal: %{y:.1f}<extra></extra>",
            )
        )

        # Linha de referência base 100
        fig.add_hline(
            y=100,
            line_dash="dot",
            line_color="rgba(255,255,255,0.4)",
            annotation_text="Média Anual (100.0)",
            annotation_position="bottom right",
            yref="y2",
        )

        fig.update_layout(
            yaxis=dict(title="Volume (MT)", showgrid=False),
            yaxis2=dict(
                title="Índice Sazonal (Base 100)",
                overlaying="y",
                side="right",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.06)",
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20),
            height=420,
        )
        apply_ferti_theme(fig, height=420)
        st.plotly_chart(fig, width="stretch", config=get_default_plotly_config())

    with tab_crops:
        st.subheader("🌾 Mapeamento de Fases das Safras Brasileiras")
        c_verao, c_safrinha = st.columns(2)

        with c_verao:
            with st.container(border=True):
                st.markdown("#### ☀️ Safra de Verão (Soja & Milho 1ª Safra)")
                st.markdown("**Período Crítico de Compras:** Maio a Agosto")
                st.markdown("**Plantio no Campo:** Setembro a Novembro")
                st.markdown("**Demanda Predominante:** Fosfatados (MAP/DAP) e Potássio (KCl)")
                st.write(
                    "Representa o maior pico de consumo anual de fertilizantes no Brasil. "
                    "Os produtores do Centro-Oeste e Sul do país concentram o recebimento nas fazendas "
                    "entre julho e setembro para adubação de plantio."
                )

        with c_safrinha:
            with st.container(border=True):
                st.markdown("#### 🌽 Safrinha (Milho 2ª Safra & Algodão)")
                st.markdown("**Período Crítico de Compras:** Outubro a Janeiro")
                st.markdown("**Plantio no Campo:** Janeiro a Março")
                st.markdown("**Demanda Predominante:** Nitrogenados (Ureia e Nitrato de Amônio)")
                st.write(
                    "Cultivo intensivo pós-colheita da soja, demandando doses maciças de nitrogênio "
                    "em cobertura. A janela de aplicação é curta e depende fortemente do regime hídrico "
                    "de verão/outono."
                )

    with tab_table:
        st.subheader("📋 Tabela Mensal de Sazonalidade")
        st.dataframe(
            df_seas.rename(columns={
                "month": "Mês",
                "month_name": "Nome",
                "average_volume_mt": "Volume Estimado (MT)",
                "seasonality_index": "Índice Sazonal",
                "peak_status": "Classificação",
                "crop_calendar_phase": "Fase Agrícola Conectada",
            }),
            column_config={
                "Volume Estimado (MT)": st.column_config.NumberColumn(format="%d MT"),
                "Índice Sazonal": st.column_config.ProgressColumn(
                    "Índice (Base 100)",
                    format="%.1f",
                    min_value=50,
                    max_value=170,
                ),
            },
            width="stretch",
            hide_index=True,
        )
        render_download_csv_button(df_seas, filename="sazonalidade_fertilizantes.csv", key="dl_p10_seas")

    render_source_badge("MDIC Comex Stat • ANDA • Conab", "Mensal")


if __name__ == "__main__":
    render_page()

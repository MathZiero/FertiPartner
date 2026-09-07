"""Tendências de Preços e Benchmarks Internacionais."""

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
    render_units_legend,
)
from app.presentation.streamlit.theme import (
    apply_ferti_theme,
    get_default_plotly_config,
    FERTI_COLORS,
)


def render_view() -> None:
    render_header(
        title="Preços & Benchmarks Internacionais",
        subtitle="Séries históricas de preços FOB e CFR, médias móveis trimestrais e volatilidade mês a mês das principais referências globais.",
        badge_text="FRED & World Bank",
        badge_type="amber",
    )

    df_prices = FertiDataService.get_price_benchmark_trends()

    if df_prices.empty:
        st.warning("Séries de preços não disponíveis.")
        return

    # Controles de filtro
    c_fert, c_bench, c_time = st.columns([4, 5, 3])
    with c_fert:
        fert_options = ["Todos"] + sorted(df_prices["fertilizer_name"].dropna().unique().tolist())
        selected_fert = st.selectbox("Fertilizante:", fert_options)

    with c_bench:
        bench_df = df_prices if selected_fert == "Todos" else df_prices[df_prices["fertilizer_name"] == selected_fert]
        bench_options = ["Todos"] + sorted(bench_df["benchmark_name"].dropna().unique().tolist())
        selected_bench = st.selectbox("Benchmark de Referência:", bench_options)

    with c_time:
        time_window = st.segmented_control("Janela Temporal", ["1A", "3A", "5A", "Tudo"], default="Tudo")
        if not time_window:
            time_window = "Tudo"

    # Filtragem
    filtered = df_prices.copy()
    if selected_fert != "Todos":
        filtered = filtered[filtered["fertilizer_name"] == selected_fert]
    if selected_bench != "Todos":
        filtered = filtered[filtered["benchmark_name"] == selected_bench]

    if filtered.empty:
        st.info("Nenhum dado de preço encontrado para esta combinação.")
        return

    # Filtro temporal
    filtered = filtered.sort_values(by="price_date")
    if time_window and time_window != "Tudo" and "price_date" in filtered.columns:
        max_date = filtered["price_date"].max()
        years_back = int(time_window.replace("A", ""))
        min_date = max_date - pd.DateOffset(years=years_back)
        filtered = filtered[filtered["price_date"] >= min_date]

    # KPIs de preço
    latest_row = filtered.iloc[-1]
    latest_price = latest_row["standard_price_usd_per_mt"]
    mom_change = latest_row.get("month_over_month_pct_change")
    moving_avg = latest_row.get("moving_avg_3m_usd")
    hub_name = latest_row.get("hub_port_name", "Mercado Global")

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(
            title="Última Cotação Registrada",
            value=f"$ {latest_price:,.2f} / MT",
            delta=f"{mom_change:+.2f}% MoM" if pd.notnull(mom_change) else None,
            delta_positive=(mom_change >= 0) if pd.notnull(mom_change) else None,
            help_text=f"Hub: {hub_name} (USD/MT = Dólares por Tonelada Métrica)",
        )
    with k2:
        render_kpi_card(
            title="Média Móvel Trimestral (3M)",
            value=f"$ {moving_avg:,.2f} / MT" if pd.notnull(moving_avg) else "N/A",
            delta="Tendência Suavizada",
            delta_positive=None,
            help_text="Média dos últimos 3 meses em Dólares por Tonelada Métrica (USD/MT)",
        )
    with k3:
        price_spread = (filtered["standard_price_usd_per_mt"].max() - filtered["standard_price_usd_per_mt"].min())
        render_kpi_card(
            title="Amplitude no Período (Spread)",
            value=f"$ {price_spread:,.2f} / MT",
            delta=f"Min: ${filtered['standard_price_usd_per_mt'].min():,.0f} | Max: ${filtered['standard_price_usd_per_mt'].max():,.0f}",
            delta_positive=None,
            help_text="Variação máx - mín no período (USD/MT)",
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Gráfico Principal de Séries Temporais com Média Móvel
    st.markdown("##### 📈 Evolução de Preços (USD / MT)")
    fig_line = go.Figure()

    for idx, (b_name, grp) in enumerate(filtered.groupby("benchmark_name")):
        color = FERTI_COLORS[idx % len(FERTI_COLORS)]
        # Linha de preço spot/mensal
        fig_line.add_trace(
            go.Scatter(
                x=grp["price_date"],
                y=grp["standard_price_usd_per_mt"],
                name=f"{b_name} (Preço)",
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                hovertemplate="<b>%{x|%b %Y}</b><br>Preço: $ %{y:,.2f}/MT<extra></extra>",
            )
        )
        # Linha tracejada da média móvel 3M se disponível
        if "moving_avg_3m_usd" in grp.columns and grp["moving_avg_3m_usd"].notnull().any():
            fig_line.add_trace(
                go.Scatter(
                    x=grp["price_date"],
                    y=grp["moving_avg_3m_usd"],
                    name=f"{b_name} (Média 3M)",
                    mode="lines",
                    line=dict(color=color, width=1.5, dash="dot"),
                    opacity=0.6,
                    hovertemplate="<b>%{x|%b %Y}</b><br>Média 3M: $ %{y:,.2f}/MT<extra></extra>",
                )
            )

    apply_ferti_theme(fig_line, height=420, x_title="Data da Cotação", y_title="USD por Tonelada Métrica (MT)")
    st.plotly_chart(fig_line, width="stretch", config=get_default_plotly_config())

    st.divider()

    # Gráfico de Variação MoM %
    st.markdown("##### 📊 Variação Mensal de Preço (%)")
    valid_mom = filtered.dropna(subset=["month_over_month_pct_change"])
    if not valid_mom.empty:
        fig_mom = px.bar(
            valid_mom,
            x="price_date",
            y="month_over_month_pct_change",
            color="month_over_month_pct_change",
            color_continuous_scale=["#F43F5E", "#64748B", "#10B981"],
            color_continuous_midpoint=0,
            labels={"price_date": "Data", "month_over_month_pct_change": "Variação MoM (%)"},
        )
        fig_mom.update_traces(texttemplate="%{y:+.1f}%", textposition="outside")
        apply_ferti_theme(fig_mom, height=280, show_legend=False)
        st.plotly_chart(fig_mom, width="stretch", config=get_default_plotly_config())

    st.divider()

    # Tabela detalhada
    st.markdown("##### 📋 Histórico Numérico de Cotações")
    display_cols = ["price_date", "fertilizer_name", "benchmark_name", "hub_port_name", "incoterm", "standard_price_usd_per_mt", "month_over_month_pct_change", "moving_avg_3m_usd"]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[available].sort_values(by="price_date", ascending=False).rename(columns={
            "price_date": "Data",
            "fertilizer_name": "Fertilizante",
            "benchmark_name": "Benchmark",
            "hub_port_name": "Porto / Hub",
            "incoterm": "Incoterm",
            "standard_price_usd_per_mt": "Preço ($/MT)",
            "month_over_month_pct_change": "Var. MoM (%)",
            "moving_avg_3m_usd": "Média 3M ($/MT)",
        }),
        column_config={
            "Preço ($/MT)": st.column_config.NumberColumn(format="$ %.2f"),
            "Média 3M ($/MT)": st.column_config.NumberColumn(format="$ %.2f"),
            "Var. MoM (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
    render_download_csv_button(filtered, filename="historico_precos.csv")

    st.divider()
    render_units_legend()
    render_source_badge("FRED (Federal Reserve) • Banco Mundial Commodity Markets", "Mensal")


if __name__ == "__main__":
    render_view()

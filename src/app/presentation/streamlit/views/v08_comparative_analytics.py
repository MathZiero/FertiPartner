"""Central de Inteligência Estratégica NPK: Análise Comparativa Multidimensional de Mercado."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_download_csv_button,
    render_header,
    render_source_badge,
    render_units_legend,
)
from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.theme import (
    FERTI_COLORS,
    apply_ferti_theme,
    get_default_plotly_config,
)
from domain.fertilizers import FERTILIZERS_CATALOG


def render_view() -> None:
    render_header(
        title="Análise Comparativa & Inteligência NPK",
        subtitle="Mecanismo analítico avançado para comparação cruzada de preços, paridades de troca, dependência externa e concentração de mercado entre Nitrogenados, Fosfatados e Potássicos.",
        badge_text="Inteligência de Mercado",
        badge_type="purple",
    )

    # Carregamento de dados analíticos
    df_prices = FertiDataService.get_price_benchmark_trends()
    df_dependency = FertiDataService.get_brazil_external_dependency()
    df_production = FertiDataService.get_global_production_rankings()
    df_uf = FertiDataService.get_brazil_uf_distribution()

    # =========================================================================
    # MÓDULO 1: COMPARADOR DINÂMICO DE PREÇOS NPK AO LONGO DO TEMPO
    # =========================================================================
    st.markdown("### 1. 📈 Comparador Dinâmico de Preços NPK ao Longo do Tempo")
    st.caption("Compare a evolução temporal das cotações em valor nominal ou em base normalizada (Base 100) para analisar a volatilidade relativa.")

    col_fil_nut, col_fil_win, col_fil_mode = st.columns([1.5, 1.2, 1.3])

    with col_fil_nut:
        nut_filter = st.selectbox(
            "Filtrar Nutriente:",
            options=["Todos os Nutrientes (N, P, K)", "Nitrogenados (N)", "Fosfatados (P)", "Potássicos (K)"],
            key="comp_nut_filter",
        )

    with col_fil_win:
        time_window = st.selectbox(
            "Janela Temporal:",
            options=["1 Ano", "2 Anos", "3 Anos", "Histórico Completo"],
            index=3,
            key="comp_time_window",
        )

    with col_fil_mode:
        view_mode = st.radio(
            "Modo de Exibição:",
            options=["Preço Nominal (USD/MT)", "Índice Base 100 (Normalizado)"],
            horizontal=True,
            key="comp_view_mode",
        )

    # Filtragem do dataframe de preços
    df_p_filtered = df_prices.copy()

    if nut_filter == "Nitrogenados (N)":
        df_p_filtered = df_p_filtered[df_p_filtered["nutrient_type"] == "Nitrogenados"]
    elif nut_filter == "Fosfatados (P)":
        df_p_filtered = df_p_filtered[df_p_filtered["nutrient_type"] == "Fosfatados"]
    elif nut_filter == "Potássicos (K)":
        df_p_filtered = df_p_filtered[df_p_filtered["nutrient_type"] == "Potássicos"]

    if not df_p_filtered.empty and "price_date" in df_p_filtered.columns:
        max_date = df_p_filtered["price_date"].max()
        if time_window == "1 Ano":
            df_p_filtered = df_p_filtered[df_p_filtered["price_date"] >= max_date - pd.DateOffset(years=1)]
        elif time_window == "2 Anos":
            df_p_filtered = df_p_filtered[df_p_filtered["price_date"] >= max_date - pd.DateOffset(years=2)]
        elif time_window == "3 Anos":
            df_p_filtered = df_p_filtered[df_p_filtered["price_date"] >= max_date - pd.DateOffset(years=3)]

    # Cálculo da Base 100 se selecionado
    y_col = "standard_price_usd_per_mt"
    y_title = "Preço Spot (USD / MT)"
    if view_mode == "Índice Base 100 (Normalizado)" and not df_p_filtered.empty:
        df_p_filtered["price_base_100"] = df_p_filtered.groupby("benchmark_name")["standard_price_usd_per_mt"].transform(
            lambda x: (x / x.iloc[0] * 100) if len(x) > 0 and x.iloc[0] > 0 else 100.0
        )
        y_col = "price_base_100"
        y_title = "Índice de Variação (Base 100 = Início do Período)"

    if not df_p_filtered.empty:
        fig_price_comp = px.line(
            df_p_filtered,
            x="price_date",
            y=y_col,
            color="benchmark_name",
            markers=True,
            labels={
                "price_date": "Data",
                y_col: y_title,
                "benchmark_name": "Benchmark Internacional",
            },
        )
        apply_ferti_theme(fig_price_comp, height=420)
        fig_price_comp.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_price_comp, width="stretch", config=get_default_plotly_config())

        # Tabela resumo de amplitude e spread
        summary_rows = []
        for bname, grp in df_p_filtered.groupby("benchmark_name"):
            p_curr = grp["standard_price_usd_per_mt"].iloc[-1]
            p_min = grp["standard_price_usd_per_mt"].min()
            p_max = grp["standard_price_usd_per_mt"].max()
            p_avg = grp["standard_price_usd_per_mt"].mean()
            p_start = grp["standard_price_usd_per_mt"].iloc[0]
            var_pct = ((p_curr - p_start) / p_start * 100) if p_start > 0 else 0.0
            summary_rows.append({
                "Benchmark": bname,
                "Nutriente": grp["nutrient_type"].iloc[0] if "nutrient_type" in grp.columns else "NPK",
                "Preço Atual ($/MT)": p_curr,
                "Mínimo Período": p_min,
                "Máximo Período": p_max,
                "Média Histórica": p_avg,
                "Variação no Período (%)": var_pct,
            })
        if summary_rows:
            df_sum = pd.DataFrame(summary_rows)
            st.dataframe(
                df_sum,
                column_config={
                    "Preço Atual ($/MT)": st.column_config.NumberColumn(format="$%.2f"),
                    "Mínimo Período": st.column_config.NumberColumn(format="$%.2f"),
                    "Máximo Período": st.column_config.NumberColumn(format="$%.2f"),
                    "Média Histórica": st.column_config.NumberColumn(format="$%.2f"),
                    "Variação no Período (%)": st.column_config.NumberColumn(format="%.2f%%"),
                },
                width="stretch",
                hide_index=True,
            )
            render_download_csv_button(df_sum, filename="comparativo_precos_npk.csv")
    else:
        st.info("Nenhum registro de preço disponível para os filtros selecionados.")

    st.divider()

    # =========================================================================
    # MÓDULO 2: RELAÇÕES DE TROCA & RATIOS ENTRE FERTILIZANTES
    # =========================================================================
    st.markdown("### 2. ⚖️ Relações de Troca & Ratios Históricos entre Fertilizantes")
    st.caption("Selecione quaisquer dois fertilizantes para comparar a paridade de preços relativa ao longo do tempo, identificar desvios da média histórica (±1σ) e diagnosticar momentos oportunos de aquisição.")

    # Pivot de preços por data para calcular paridades
    pivoted_prices = df_prices.pivot_table(
        index="price_date",
        columns="fertilizer_name",
        values="standard_price_usd_per_mt",
        aggfunc="mean",
    ).dropna()

    if not pivoted_prices.empty and len(pivoted_prices.columns) >= 2:
        available_price_ferts = list(pivoted_prices.columns)

        col_sel_a, col_sel_b = st.columns(2)
        with col_sel_a:
            # Numerador: prioriza DAP ou MAP se disponível
            def_a_idx = next((i for i, name in enumerate(available_price_ferts) if "DAP" in name or "MAP" in name), 0)
            fert_a = st.selectbox(
                "Fertilizante Numerador (A):",
                options=available_price_ferts,
                index=def_a_idx,
                key="comp_ratio_fert_a",
                help="O preço deste fertilizante ficará no numerador da fração (A ÷ B).",
            )

        with col_sel_b:
            # Denominador: prioriza Ureia se disponível
            def_b_idx = next((i for i, name in enumerate(available_price_ferts) if "Ureia" in name), 1 if len(available_price_ferts) > 1 else 0)
            fert_b = st.selectbox(
                "Fertilizante Denominador (B):",
                options=available_price_ferts,
                index=def_b_idx,
                key="comp_ratio_fert_b",
                help="O preço deste fertilizante servirá como base comparativa de valor no denominador.",
            )

        if fert_a == fert_b:
            st.info(f"Você selecionou o mesmo fertilizante ({fert_a}) como numerador e denominador. A paridade entre o mesmo insumo é unitária e constante (1.00x).")
            ratio_series = pd.Series(1.0, index=pivoted_prices.index)
            ratio_label = f"Ratio: {fert_a} ÷ {fert_b} (1.00x)"
        else:
            ratio_series = (pivoted_prices[fert_a] / pivoted_prices[fert_b]).dropna()
            ratio_label = f"Ratio: {fert_a} ÷ {fert_b}"

        if not ratio_series.empty:
            curr_ratio = float(ratio_series.iloc[-1])
            avg_ratio = float(ratio_series.mean())
            std_ratio = float(ratio_series.std()) if len(ratio_series) > 1 else 0.05
            upper_bound = avg_ratio + std_ratio
            lower_bound = max(0.0, avg_ratio - std_ratio)

            if fert_a == fert_b:
                status_text = "Paridade Unitária Neutra (Mesmo Produto)"
                badge_class = "fp-badge-emerald"
            elif curr_ratio > upper_bound:
                status_text = f"{fert_a} Sobrevalorizado vs {fert_b} (Prêmio Acima de +1σ Histórico)"
                badge_class = "fp-badge-amber"
            elif curr_ratio < lower_bound:
                status_text = f"{fert_a} Subvalorizado vs {fert_b} (Oportunidade Histórica Abaixo de -1σ)"
                badge_class = "fp-badge-blue"
            else:
                status_text = f"Paridade em Equilíbrio Histórico (Dentro da Faixa Típica ±1σ)"
                badge_class = "fp-badge-emerald"

            st.markdown(
                f"""
                <div style="background: #F8FAF9; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem 1.25rem; margin-top: 0.5rem; margin-bottom: 1.25rem;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #52796F; text-transform: uppercase;">Diagnóstico Estatístico de Paridade</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #1B4332; margin: 0.35rem 0;">
                        Ratio Atual: {curr_ratio:.2f}x 
                        <span style="font-size: 0.88rem; font-weight: 500; color: #6B7280;">(Média Histórica: {avg_ratio:.2f}x | Faixa Normal: {lower_bound:.2f}x — {upper_bound:.2f}x)</span>
                    </div>
                    <span class="fp-badge {badge_class}">{status_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fig_ratio = go.Figure()

            # Bandas de desvio padrão
            fig_ratio.add_trace(go.Scatter(
                x=ratio_series.index,
                y=[upper_bound] * len(ratio_series),
                mode="lines",
                line=dict(color="rgba(180, 83, 9, 0.4)", dash="dot", width=1.2),
                name=f"+1σ ({upper_bound:.2f}x)",
                showlegend=True,
            ))
            fig_ratio.add_trace(go.Scatter(
                x=ratio_series.index,
                y=[lower_bound] * len(ratio_series),
                mode="lines",
                line=dict(color="rgba(180, 83, 9, 0.4)", dash="dot", width=1.2),
                fill="tonexty",
                fillcolor="rgba(245, 158, 11, 0.08)",
                name=f"-1σ ({lower_bound:.2f}x)",
                showlegend=True,
            ))
            # Linha Média
            fig_ratio.add_trace(go.Scatter(
                x=ratio_series.index,
                y=[avg_ratio] * len(ratio_series),
                mode="lines",
                line=dict(color="#6B7280", dash="dash", width=1.5),
                name=f"Média Histórica ({avg_ratio:.2f}x)",
            ))
            # Linha do Ratio Real
            fig_ratio.add_trace(go.Scatter(
                x=ratio_series.index,
                y=ratio_series.values,
                mode="lines+markers",
                line=dict(color=FERTI_COLORS[0], width=2.5),
                marker=dict(size=5),
                name=ratio_label,
            ))

            apply_ferti_theme(fig_ratio, height=380)
            fig_ratio.update_layout(
                yaxis_title=f"Ratio de Troca: {fert_a} ÷ {fert_b} (x)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_ratio, width="stretch", config=get_default_plotly_config())
        else:
            st.info("Séries históricas insuficientes para calcular a paridade selecionada.")
    else:
        st.info("Séries de preços insuficientes na base de dados para cálculo de paridades.")

    st.divider()

    # =========================================================================
    # MÓDULO 3: MATRIZ DE DEPENDÊNCIA EXTERNA & BALANÇO FÍSICO NACIONAL
    # =========================================================================
    st.markdown("### 3. 🌐 Balanço Físico Nacional & Taxa de Dependência Externa")
    st.caption("Comparação entre consumo aparente, produção local e importações para cada classe de fertilizante no Brasil.")

    if not df_dependency.empty:
        # Pega o ano mais recente consolidado
        years_dep = sorted(df_dependency["ref_year"].dropna().unique().astype(int).tolist(), reverse=True)
        selected_dep_year = st.selectbox("Ano de Referência:", years_dep, index=0, key="comp_dep_year")

        df_dep_y = df_dependency[df_dependency["ref_year"] == selected_dep_year].copy()

        c_dep_chart, c_dep_table = st.columns([1.8, 1.2])

        with c_dep_chart:
            # Gráfico de barras horizontais comparando Produção vs Importação
            df_dep_melt = df_dep_y.melt(
                id_vars=["fertilizer_name"],
                value_vars=["national_production_mt", "total_imports_mt"],
                var_name="Tipo",
                value_name="Quantidade (MT)",
            )
            df_dep_melt["Tipo"] = df_dep_melt["Tipo"].map({
                "national_production_mt": "Produção Nacional",
                "total_imports_mt": "Importações",
            })

            fig_dep = px.bar(
                df_dep_melt,
                x="Quantidade (MT)",
                y="fertilizer_name",
                color="Tipo",
                orientation="h",
                barmode="stack",
                color_discrete_map={"Produção Nacional": "#2D6A4F", "Importações": "#3B82F6"},
                labels={"fertilizer_name": "Fertilizante", "Quantidade (MT)": "Volume (MT)"},
            )
            apply_ferti_theme(fig_dep, height=340)
            fig_dep.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_dep, width="stretch", config=get_default_plotly_config())

        with c_dep_table:
            st.markdown("###### 📊 Grau de Vulnerabilidade Externa")
            st.dataframe(
                df_dep_y[["fertilizer_name", "apparent_consumption_mt", "external_dependency_pct"]].rename(columns={
                    "fertilizer_name": "Produto",
                    "apparent_consumption_mt": "Consumo (MT)",
                    "external_dependency_pct": "Dependência (%)",
                }),
                column_config={
                    "Consumo (MT)": st.column_config.NumberColumn(format="%d MT"),
                    "Dependência (%)": st.column_config.ProgressColumn(
                        format="%.1f%%",
                        min_value=0.0,
                        max_value=100.0,
                    ),
                },
                width="stretch",
                hide_index=True,
            )

    st.divider()

    # =========================================================================
    # MÓDULO 4: CONCENTRAÇÃO GLOBAL DE FORNECIMENTO & RISCO GEOPOLÍTICO (HHI)
    # =========================================================================
    st.markdown("### 4. 🚢 Concentração de Fornecimento Global & Risco Geopolítico (Índice HHI)")
    st.caption("Avaliação do grau de oligopólio ou dispersão entre países produtores mundiais para N, P e K.")

    if not df_production.empty:
        ferts_prod = sorted(df_production["fertilizer_name"].dropna().unique().tolist())
        sel_fert_hhi = st.selectbox("Escolha o Produto para Avaliar Concentração:", ferts_prod, index=0, key="comp_hhi_fert")

        df_prod_f = df_production[df_production["fertilizer_name"] == sel_fert_hhi].copy()
        if not df_prod_f.empty:
            latest_prod_year = int(df_prod_f["production_year"].max())
            df_prod_fy = df_prod_f[df_prod_f["production_year"] == latest_prod_year].sort_values("standard_quantity_mt", ascending=False)

            # Cálculo do Índice Herfindahl-Hirschman (HHI): soma dos quadrados das fatias percentuais
            hhi_score = float((df_prod_fy["global_market_share_pct"] ** 2).sum())

            hhi_class = "Baixa Concentração (Mercado Competitivo)"
            hhi_color = "emerald"
            if hhi_score > 2500:
                hhi_class = "Alta Concentração (Oligopólio / Risco Geopolítico Elevado)"
                hhi_color = "purple"
            elif hhi_score > 1500:
                hhi_class = "Concentração Moderada"
                hhi_color = "amber"

            c_hhi_kpi, c_hhi_donut = st.columns([1.2, 1.8])

            with c_hhi_kpi:
                st.markdown(
                    f"""
                    <div style="background: #F8FAF9; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.25rem; margin-top: 1rem;">
                        <div style="font-size: 0.8rem; font-weight: 700; color: #52796F; text-transform: uppercase;">Índice Herfindahl-Hirschman</div>
                        <div style="font-size: 2.2rem; font-weight: 800; color: #1B4332; margin: 0.25rem 0;">{hhi_score:,.0f} pts</div>
                        <span class="fp-badge fp-badge-{hhi_color}">{hhi_class}</span>
                        <p style="font-size: 0.85rem; color: #4B5563; margin-top: 0.75rem;">
                            O HHI avalia o risco de cartelização e choques de suprimento. Mercados com HHI acima de 2.500 sofrem forte influência de poucos governos.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_hhi_donut:
                top5_df = df_prod_fy.head(5).copy()
                others_vol = df_prod_fy.iloc[5:]["standard_quantity_mt"].sum() if len(df_prod_fy) > 5 else 0.0
                if others_vol > 0:
                    top5_df = pd.concat([
                        top5_df,
                        pd.DataFrame([{
                            "country_name": "Demais Produtores",
                            "standard_quantity_mt": others_vol,
                            "global_market_share_pct": (others_vol / df_prod_fy["standard_quantity_mt"].sum() * 100),
                        }]),
                    ], ignore_index=True)

                fig_donut = px.pie(
                    top5_df,
                    names="country_name",
                    values="standard_quantity_mt",
                    hole=0.45,
                    color_discrete_sequence=px.colors.sequential.Aggrnyl_r,
                )
                apply_ferti_theme(fig_donut, height=330)
                st.plotly_chart(fig_donut, width="stretch", config=get_default_plotly_config())

    st.divider()

    # =========================================================================
    # MÓDULO 5: DISTRIBUIÇÃO E DEMANDA REGIONAL POR ESTADO (UF)
    # =========================================================================
    st.markdown("### 5. 🗺️ Distribuição Interestadual & Demanda Regional no Brasil")
    st.caption("Concentração das entregas de fertilizantes aos consumidores finais por unidade federativa.")

    if not df_uf.empty:
        c_uf_chart, c_uf_insight = st.columns([1.8, 1.2])

        with c_uf_chart:
            df_uf_sorted = df_uf.sort_values("share_pct", ascending=True)
            fig_uf = px.bar(
                df_uf_sorted,
                x="share_pct",
                y="state_name",
                orientation="h",
                text="share_pct",
                color="share_pct",
                color_continuous_scale="Greens",
                labels={"share_pct": "Participação no Consumo Nacional (%)", "state_name": "Estado"},
            )
            fig_uf.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            apply_ferti_theme(fig_uf, height=380)
            fig_uf.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_uf, width="stretch", config=get_default_plotly_config())

        with c_uf_insight:
            st.markdown("###### 🌾 Principais Polos de Consumo")
            st.markdown(
                """
                - **Centro-Oeste (Mato Grosso & Goiás)**: Representa mais de 38% da demanda total do país, impulsionada pelo cultivo intensivo de soja de primeira safra e milho safrinha.
                - **Sul (Paraná & Rio Grande do Sul)**: Respondem por cerca de 26% do consumo, com expressiva aplicação em trigo de inverno e grãos.
                - **Matopiba & Cerrado**: Regiões de expansão contínua com elevada necessidade de fosfatados e corretivos para solos sob estresse hídrico.
                """
            )
            render_download_csv_button(df_uf, filename="distribuicao_uf_fertilizantes.csv")

    st.divider()

    # =========================================================================
    # MÓDULO 6: MATRIZ ESTATÍSTICA DE CORRELAÇÃO & VOLATILIDADE
    # =========================================================================
    st.markdown("### 6. ⚡ Matriz Estatística de Correlação e Volatilidade entre Fertilizantes")
    st.caption("Coeficiente de correlação linear de Pearson e dispersão histórica dos preços para todos os fertilizantes do portfólio.")

    # Catálogo completo de fertilizantes do sistema
    catalog_items = [
        {"name": "Ureia", "query": ["ureia"]},
        {"name": "Amônia Anidra", "query": ["amônia", "amonia"]},
        {"name": "Nitrato Amônio", "query": ["nitrato"]},
        {"name": "Sulfato Amônio", "query": ["sulfato de am"]},
        {"name": "MAP", "query": ["map", "monoamônico", "monoamonico"]},
        {"name": "DAP", "query": ["dap", "diamônico", "diamonico"]},
        {"name": "SSP", "query": ["ssp", "superfosfato simples"]},
        {"name": "TSP", "query": ["tsp", "superfosfato triplo"]},
        {"name": "Rocha Fosfática", "query": ["rocha"]},
        {"name": "KCl", "query": ["kcl", "potássio", "potassio"]},
        {"name": "SOP", "query": ["sop", "sulfato de pot"]},
        {"name": "Enxofre", "query": ["enxofre"]},
        {"name": "Micronutrientes", "query": ["micronutrientes"]},
    ]

    # Mapeamento de quais fertilizantes possuem séries de preços em pivoted_prices
    fert_col_map: dict[str, str | None] = {}
    for item in catalog_items:
        fname = item["name"]
        matched_col = None
        if not pivoted_prices.empty:
            for col in pivoted_prices.columns:
                col_l = col.lower()
                if any(q in col_l for q in item["query"]):
                    matched_col = col
                    break
        fert_col_map[fname] = matched_col

    all_names = [item["name"] for item in catalog_items]
    n_total = len(all_names)
    z_base = [[0 for _ in range(n_total)] for _ in range(n_total)]
    z_corr: list[list[float | None]] = [[None for _ in range(n_total)] for _ in range(n_total)]
    annotations = []

    for i, row_name in enumerate(all_names):
        col_i = fert_col_map.get(row_name)
        for j, col_name in enumerate(all_names):
            col_j = fert_col_map.get(col_name)
            val = None
            if col_i is not None and col_j is not None and not pivoted_prices.empty:
                if i == j:
                    val = 1.0
                else:
                    s_i = pivoted_prices[col_i]
                    s_j = pivoted_prices[col_j]
                    c_val = s_i.corr(s_j)
                    if pd.notna(c_val):
                        val = round(float(c_val), 2)
            z_corr[i][j] = val

            if val is None:
                txt = "N/D"
                txt_color = "#94A3B8"
            else:
                txt = f"{val:+.2f}" if val != 1.0 else "1.00"
                txt_color = "#FFFFFF" if abs(val) > 0.65 else "#1E293B"

            annotations.append(dict(
                x=all_names[j],
                y=all_names[i],
                text=txt,
                showarrow=False,
                font=dict(color=txt_color, size=9),
            ))

    c_corr_heat, c_vol_tbl = st.columns([1.8, 1.2])

    with c_corr_heat:
        fig_corr = go.Figure()

        # Camada 1: Células neutras de fundo para indicar ausência de dados
        fig_corr.add_trace(go.Heatmap(
            x=all_names,
            y=all_names,
            z=z_base,
            colorscale=[[0, "#F1F5F9"], [1, "#F1F5F9"]],
            showscale=False,
            hoverinfo="skip",
            xgap=2,
            ygap=2,
        ))

        # Camada 2: Células com coeficientes de correlação reais calculados
        fig_corr.add_trace(go.Heatmap(
            x=all_names,
            y=all_names,
            z=z_corr,
            colorscale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            xgap=2,
            ygap=2,
            colorbar=dict(
                title="Pearson (r)",
                thickness=14,
                len=0.85,
                tickvals=[-1.0, -0.5, 0.0, 0.5, 1.0],
                ticktext=["-1.0 (Inversa)", "-0.5", "0.0 (Neutra)", "+0.5", "+1.0 (Direta)"],
            ),
            hovertemplate="%{y} vs %{x}<br>Correlação (r): %{z:.2f}<extra></extra>",
        ))

        apply_ferti_theme(fig_corr, height=520)
        fig_corr.update_layout(
            annotations=annotations,
            xaxis=dict(tickangle=-45, side="bottom"),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_corr, width="stretch", config=get_default_plotly_config())

        # Legenda explicativa explícita e clara sobre células neutras N/D
        st.markdown(
            """
            <div style="background: #F8FAF9; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem 1.1rem; margin-top: 0.5rem; margin-bottom: 0.5rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #1B4332; margin-bottom: 0.35rem;">
                    📖 Interpretação da Matriz de Correlação Multidimensional
                </div>
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.5;">
                    • <b style="color: #2563EB;">Escala Colorida (-1.00 a +1.00):</b> Coeficiente de correlação de Pearson entre as cotações históricas de preços internacionais. Valores próximos a <b>+1.00</b> indicam tendência forte de movimentação conjunta; valores negativos indicam dinâmicas divergentes de mercado.<br>
                    • <b style="color: #64748B;">Células em Cinza Neutro (N/D):</b> <i>Sem dados históricos suficientes para correlacionar.</i> Abrange fertilizantes cadastrados no banco de dados (ex.: Amônia Anidra, Nitrato de Amônio, Sulfatos, Superfosfatos, Rocha, SOP e Micronutrientes) que atualmente não contam com séries spot internacionais ativas para pareamento temporal direto.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_vol_tbl:
        if not pivoted_prices.empty and len(pivoted_prices.columns) > 1:
            vol_records = []
            for cname in pivoted_prices.columns:
                series = pivoted_prices[cname].dropna()
                mean_v = series.mean()
                std_v = series.std()
                cov_pct = (std_v / mean_v * 100) if mean_v > 0 else 0.0
                vol_records.append({
                    "Fertilizante": cname,
                    "Preço Médio": mean_v,
                    "Desvio Padrão": std_v,
                    "Volatilidade (CV %)": cov_pct,
                })
            df_vol = pd.DataFrame(vol_records).sort_values("Volatilidade (CV %)", ascending=False)
            st.markdown("###### 📊 Ranking de Volatilidade de Preços")
            st.caption("Calculado sobre os produtos com séries temporais de preços ativas.")
            st.dataframe(
                df_vol,
                column_config={
                    "Preço Médio": st.column_config.NumberColumn(format="$%.2f"),
                    "Desvio Padrão": st.column_config.NumberColumn(format="$%.2f"),
                    "Volatilidade (CV %)": st.column_config.ProgressColumn(
                        format="%.1f%%",
                        min_value=0.0,
                        max_value=100.0,
                    ),
                },
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Dados insuficientes para ranking de volatilidade.")

    st.divider()
    render_units_legend()
    render_source_badge("Inteligência FertiPartner NPK", "Consolidado")


if __name__ == "__main__":
    render_view()

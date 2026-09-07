"""View modular para páginas dedicadas de fertilizantes individuais.

Página única alongada com gráficos e mapas replicados, dotados de filtros independentes
por componente, mapa global com suporte a Produção, Exportação e Importação, e menu
de navegação rápida na sidebar.
"""

from typing import Any
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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
    format_currency_usd,
    format_metric_tons,
    FERTI_COLORS,
)


def _render_sidebar_quick_jump(fert_name: str) -> None:
    """Renderiza links de navegação rápida na barra lateral para as seções da página."""
    with st.sidebar:
        st.markdown(f"#### 🧭 Navegação — {fert_name}")
        st.markdown(
            """
            <div style="font-size: 0.88rem; line-height: 1.8;">
                <a href="#producao-global" style="text-decoration: none; color: #1B4332; font-weight: 600;">🌍 1. Produção Global & Mapa</a><br>
                <a href="#comercio-internacional" style="text-decoration: none; color: #1B4332; font-weight: 600;">🚢 2. Comércio Internacional & Sankey</a><br>
                <a href="#precos-benchmarks" style="text-decoration: none; color: #1B4332; font-weight: 600;">📈 3. Preços & Benchmarks</a><br>
                <a href="#mercado-brasileiro" style="text-decoration: none; color: #1B4332; font-weight: 600;">🇧🇷 4. Mercado Brasileiro</a><br>
                <a href="#ficha-tecnica" style="text-decoration: none; color: #1B4332; font-weight: 600;">📋 5. Ficha Técnica Completa</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()


def _render_hero_specs(fert: dict[str, Any]) -> None:
    """Renderiza especificações agronômicas e químicas de destaque no topo da página."""
    chem = fert.get("chemical_formula", "N/D")
    cas = fert.get("cas_rn", "N/D")
    codes = fert.get("hs_ncm_codes") or []
    codes_str = " • ".join(codes) if codes else "N/D"
    nutrients = fert.get("typical_nutrients") or {}

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 3, 3, 3])
        with c1:
            st.caption("Fórmula Química")
            st.markdown(f"<p style='font-size: 1.15rem; font-weight: 700; color: #1B4332; margin:0;'>{chem}</p>", unsafe_allow_html=True)
        with c2:
            st.caption("Número CAS (RN)")
            st.markdown(f"<p style='font-size: 1.15rem; font-weight: 700; color: #2D6A4F; margin:0;'>{cas}</p>", unsafe_allow_html=True)
        with c3:
            st.caption("Classificação Fiscal (NCM/HS)")
            st.markdown(f"<p style='font-size: 1.05rem; font-weight: 600; color: #374151; margin:0;'>{codes_str}</p>", unsafe_allow_html=True)
        with c4:
            st.caption("Garantia Nutricional Típica")
            if nutrients and isinstance(nutrients, dict):
                badges = " ".join([
                    f"<span style='background:#E8F5E9; color:#166534; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.85rem;'>{k}: {v}%</span>"
                    for k, v in nutrients.items()
                ])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#9CA3AF;'>Não declarada</span>", unsafe_allow_html=True)


def _render_section_production(fert: dict[str, Any], slug: str) -> None:
    """Seção 1: Produção Global, Mapa Coroplético com filtros de Tipo/Ano e Ranking."""
    st.markdown('<div id="producao-global"></div>', unsafe_allow_html=True)
    st.markdown("### 🌍 1. Produção Global & Mapa Interativo")
    st.caption("Mapeamento geográfico da oferta mundial com filtros individuais para tipo de fluxo e ano de referência.")

    canonical_name = fert.get("canonical_name", "Fertilizante")

    # Controles exclusivos do Mapa Global
    with st.container(border=True):
        st.markdown("##### 🗺️ Mapa Global de Fluxos e Oferta")
        col_type, col_year = st.columns([7, 5])
        with col_type:
            flow_type = st.segmented_control(
                "Tipo de Fluxo Geográfico:",
                ["Produção", "Exportação", "Importação"],
                default="Produção",
                key=f"sec_map_type_{slug}",
            )
            if not flow_type:
                flow_type = "Produção"

        with col_year:
            years = FertiDataService.get_years_for_flow_type(flow_type, canonical_name)
            map_year = st.selectbox(
                "Ano de Referência do Mapa:",
                years,
                index=0,
                key=f"sec_map_year_{slug}",
            )

        df_map = FertiDataService.get_global_map_data(canonical_name, map_year, flow_type)

        if not df_map.empty and "country_iso3" in df_map.columns:
            color_scales = {
                "Produção": "Viridis",
                "Exportação": "Blues",
                "Importação": "Teal",
            }
            c_scale = color_scales.get(flow_type, "Viridis")

            total_val = df_map["standard_quantity_mt"].sum()
            top_country = df_map.sort_values(by="standard_quantity_mt", ascending=False).iloc[0]

            k1, k2, k3 = st.columns(3)
            with k1:
                render_kpi_card(
                    title=f"Total em {flow_type}",
                    value=format_metric_tons(total_val),
                    delta=f"{canonical_name} ({map_year})",
                    delta_positive=True,
                    help_text=f"Volume total mundial registrado de {flow_type.lower()} para {canonical_name}",
                )
            with k2:
                render_kpi_card(
                    title=f"Líder em {flow_type}",
                    value=str(top_country["country_name"]),
                    delta=f"{top_country['global_market_share_pct']:.1f}% Share",
                    delta_positive=True,
                    help_text="País com maior volume registrado",
                )
            with k3:
                render_kpi_card(
                    title="Países no Mapeamento",
                    value=f"{df_map['country_name'].nunique()} Países",
                    delta="Cobertura Global",
                    delta_positive=None,
                    help_text="Total de origens/destinos consolidados",
                )

            fig_map = px.choropleth(
                df_map,
                locations="country_iso3",
                color="standard_quantity_mt",
                hover_name="country_name",
                hover_data={
                    "standard_quantity_mt": ":,.0f",
                    "global_market_share_pct": ":.2f",
                    "country_iso3": False,
                },
                labels={
                    "standard_quantity_mt": f"{flow_type} (MT)",
                    "global_market_share_pct": "Market Share (%)",
                },
                color_continuous_scale=c_scale,
                projection="natural earth",
            )
            fig_map.update_geos(
                showcountries=True,
                countrycolor="#000000",
                countrywidth=0.7,
                showcoastlines=True,
                coastlinecolor="#000000",
                coastlinewidth=0.7,
                showland=True,
                landcolor="#F1F5F9",
                showocean=True,
                oceancolor="#F8FAFC",
                showlakes=True,
                lakecolor="#F8FAFC",
                showframe=True,
                framecolor="#000000",
                framewidth=1.0,
                bgcolor="rgba(0,0,0,0)",
            )
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=10, b=10),
                height=460,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1B4332"),
            )
            st.plotly_chart(fig_map, use_container_width=True, config=get_default_plotly_config())
        else:
            st.info(f"Sem dados geográficos de {flow_type.lower()} para {canonical_name} no ano {map_year}.")

    # Card do Ranking dos Maiores Produtores com filtro próprio
    with st.container(border=True):
        st.markdown("##### 🏆 Ranking Mundial de Produtores")
        df_prod = FertiDataService.get_global_production_rankings()
        if not df_prod.empty:
            df_p_fert = df_prod[df_prod["fertilizer_name"].astype(str).str.contains(canonical_name, case=False, na=False) | (df_prod["fertilizer_name"] == canonical_name)]
            prod_years = sorted(df_p_fert["production_year"].dropna().unique().astype(int).tolist(), reverse=True) if not df_p_fert.empty else [2024, 2023, 2022]

            c_ry, _ = st.columns([4, 8])
            with c_ry:
                rank_year = st.selectbox("Ano de Referência do Ranking:", prod_years, index=0, key=f"sec_rank_year_{slug}")

            filtered_rank = df_p_fert[df_p_fert["production_year"] == rank_year] if not df_p_fert.empty else pd.DataFrame()

            if not filtered_rank.empty:
                col_chart, col_tbl = st.columns([6, 6])
                with col_chart:
                    sorted_prod = filtered_rank.sort_values(by="standard_quantity_mt", ascending=True)
                    fig_bar = px.bar(
                        sorted_prod,
                        x="standard_quantity_mt",
                        y="country_name",
                        orientation="h",
                        labels={"standard_quantity_mt": "Volume em Toneladas (MT)", "country_name": "País"},
                        color="standard_quantity_mt",
                        color_continuous_scale="Viridis",
                    )
                    fig_bar.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
                    apply_ferti_theme(fig_bar, height=350, show_legend=False)
                    st.plotly_chart(fig_bar, use_container_width=True, config=get_default_plotly_config())

                with col_tbl:
                    display_tbl = filtered_rank[["rank_position", "country_name", "standard_quantity_mt", "global_market_share_pct"]].sort_values(by="rank_position")
                    st.dataframe(
                        display_tbl.rename(columns={
                            "rank_position": "Posição",
                            "country_name": "País",
                            "standard_quantity_mt": "Volume (MT)",
                            "global_market_share_pct": "Participação (%)",
                        }),
                        column_config={
                            "Participação (%)": st.column_config.ProgressColumn(
                                "Market Share",
                                format="%.2f%%",
                                min_value=0,
                                max_value=100,
                            ),
                            "Volume (MT)": st.column_config.NumberColumn(
                                "Volume (MT)",
                                format="%d MT",
                            ),
                        },
                        use_container_width=True,
                        hide_index=True,
                    )
                    render_download_csv_button(display_tbl, filename=f"ranking_producao_{slug}_{rank_year}.csv")
            else:
                st.info(f"Sem dados detalhados de ranking de produção para {canonical_name} no ano {rank_year}.")
        else:
            st.info("Dados de produção global indisponíveis no momento.")

    st.divider()


def _render_section_trade(fert: dict[str, Any], slug: str) -> None:
    """Seção 2: Comércio Internacional, Fluxos Sankey e Rotas Bilaterais com filtros independentes."""
    st.markdown('<div id="comercio-internacional"></div>', unsafe_allow_html=True)
    st.markdown("### 🚢 2. Comércio Internacional & Fluxos Sankey")
    st.caption("Relações bilaterais transfronteiriças, volumes de comércio e diagramas de rotas comerciais.")

    canonical_name = fert.get("canonical_name", "Fertilizante")
    df_trade = FertiDataService.get_bilateral_trade_flows()

    df_t_fert = pd.DataFrame()
    if not df_trade.empty and "fertilizer_name" in df_trade.columns:
        df_t_fert = df_trade[df_trade["fertilizer_name"].astype(str).str.contains(canonical_name, case=False, na=False) | (df_trade["fertilizer_name"] == canonical_name)].copy()

    # Bloco 1: Diagrama Sankey
    with st.container(border=True):
        st.markdown("##### 🌊 Diagrama de Fluxos Bilaterais (Sankey)")
        c_sy, c_sm = st.columns([5, 7])
        trade_years = sorted(df_t_fert["trade_year"].dropna().unique().astype(int).tolist(), reverse=True) if not df_t_fert.empty else [2024, 2023, 2022]
        with c_sy:
            sankey_year = st.selectbox("Ano de Referência:", trade_years, index=0, key=f"sec_sankey_year_{slug}")
        with c_sm:
            sankey_metric = st.radio(
                "Ponderação das Rotas:",
                ["Volume (MT)", "Valor (USD)"],
                horizontal=True,
                key=f"sec_sankey_metric_{slug}",
            )

        filtered_sankey = df_t_fert[df_t_fert["trade_year"] == sankey_year] if not df_t_fert.empty else pd.DataFrame()

        if not filtered_sankey.empty:
            agg_col = "total_quantity_mt" if "Volume" in sankey_metric else "total_value_usd"
            routes = filtered_sankey.groupby(["exporter_country", "importer_country"])[agg_col].sum().reset_index()
            routes = routes[routes[agg_col] > 0].sort_values(by=agg_col, ascending=False).head(10)

            if not routes.empty:
                exporters = sorted(routes["exporter_country"].unique().tolist())
                importers = sorted(routes["importer_country"].unique().tolist())
                node_labels = exporters + importers
                node_indices = {name: i for i, name in enumerate(node_labels)}

                sources = [node_indices[exp] for exp in routes["exporter_country"]]
                targets = [node_indices[imp] for imp in routes["importer_country"]]
                values = routes[agg_col].tolist()

                node_colors = ["#3B82F6" if i < len(exporters) else "#10B981" for i in range(len(node_labels))]
                link_colors = ["rgba(59, 130, 246, 0.40)" for _ in values]

                fig_sankey = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=18,
                        thickness=20,
                        line=dict(color="rgba(255,255,255,0.2)", width=0.5),
                        label=[f"{name} ({'Origem' if i < len(exporters) else 'Destino'})" for i, name in enumerate(node_labels)],
                        color=node_colors,
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                        color=link_colors,
                        hovertemplate=(
                            "<b>Origem:</b> %{source.label}<br>"
                            "<b>Destino:</b> %{target.label}<br>"
                            + ("<b>Volume:</b> %{value:,.0f} MT<extra></extra>" if "Volume" in sankey_metric else "<b>Valor:</b> $ %{value:,.2f} USD<extra></extra>")
                        ),
                    ),
                )])
                apply_ferti_theme(fig_sankey, title=f"Top Rotas de {canonical_name} ({sankey_year})", height=450, show_legend=False)
                fig_sankey.update_layout(margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_sankey, use_container_width=True, config=get_default_plotly_config())
            else:
                st.info(f"Sem fluxos bilaterais significativos de {canonical_name} para {sankey_year}.")
        else:
            st.info(f"Sem registros aduaneiros de comércio para {canonical_name} em {sankey_year}.")

    # Bloco 2: Origens e Destinos Globais
    with st.container(border=True):
        st.markdown("##### 🌐 Países Exportadores (Origem) e Importadores (Destino)")
        c_by, _ = st.columns([4, 8])
        with c_by:
            bar_year = st.selectbox("Ano de Análise Aduaneira:", trade_years, index=0, key=f"sec_bar_trade_year_{slug}")

        filtered_trade = df_t_fert[df_t_fert["trade_year"] == bar_year] if not df_t_fert.empty else pd.DataFrame()

        if not filtered_trade.empty:
            c_exp, c_imp = st.columns(2)
            with c_exp:
                st.markdown("###### 🚢 Maiores Origens (Exportadores)")
                exp_summary = filtered_trade.groupby("exporter_country")["total_quantity_mt"].sum().reset_index()
                exp_summary = exp_summary.sort_values(by="total_quantity_mt", ascending=True).tail(8)
                fig_exp = px.bar(
                    exp_summary,
                    x="total_quantity_mt",
                    y="exporter_country",
                    orientation="h",
                    labels={"total_quantity_mt": "Volume (MT)", "exporter_country": "País Exportador"},
                    color="total_quantity_mt",
                    color_continuous_scale="Blues",
                )
                fig_exp.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
                apply_ferti_theme(fig_exp, height=320, show_legend=False)
                st.plotly_chart(fig_exp, use_container_width=True, config=get_default_plotly_config())

            with c_imp:
                st.markdown("###### 📥 Maiores Destinos (Importadores)")
                imp_summary = filtered_trade.groupby("importer_country")["total_quantity_mt"].sum().reset_index()
                imp_summary = imp_summary.sort_values(by="total_quantity_mt", ascending=True).tail(8)
                fig_imp = px.bar(
                    imp_summary,
                    x="total_quantity_mt",
                    y="importer_country",
                    orientation="h",
                    labels={"total_quantity_mt": "Volume (MT)", "importer_country": "País Importador"},
                    color="total_quantity_mt",
                    color_continuous_scale="Teal",
                )
                fig_imp.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
                apply_ferti_theme(fig_imp, height=320, show_legend=False)
                st.plotly_chart(fig_imp, use_container_width=True, config=get_default_plotly_config())

            st.markdown("###### 📑 Relações Comerciais Consolidadas")
            disp_cols = ["exporter_country", "importer_country", "total_quantity_mt", "total_value_usd", "avg_usd_per_mt"]
            avail_cols = [c for c in disp_cols if c in filtered_trade.columns]
            st.dataframe(
                filtered_trade[avail_cols].rename(columns={
                    "exporter_country": "Origem",
                    "importer_country": "Destino",
                    "total_quantity_mt": "Volume (MT)",
                    "total_value_usd": "Valor (USD)",
                    "avg_usd_per_mt": "Preço Médio (USD/MT)",
                }),
                use_container_width=True,
                hide_index=True,
            )
            render_download_csv_button(filtered_trade[avail_cols], filename=f"comercio_{slug}_{bar_year}.csv")
        else:
            st.info(f"Sem dados detalhados de transações comerciais para {canonical_name} no ano {bar_year}.")

    st.divider()


def _render_section_prices(fert: dict[str, Any], slug: str) -> None:
    """Seção 3: Preços Internacionais e Benchmarks com controles próprios de Referência e Janela Temporal."""
    st.markdown('<div id="precos-benchmarks"></div>', unsafe_allow_html=True)
    st.markdown("### 📈 3. Preços & Benchmarks Internacionais")
    st.caption("Cotações históricas internacionais (FOB/CFR), médias móveis e spreads de mercado.")

    canonical_name = fert.get("canonical_name", "Fertilizante")
    df_prices = FertiDataService.get_price_benchmark_trends()

    df_p_fert = pd.DataFrame()
    if not df_prices.empty and "fertilizer_name" in df_prices.columns:
        df_p_fert = df_prices[df_prices["fertilizer_name"].astype(str).str.contains(canonical_name, case=False, na=False) | (df_prices["fertilizer_name"] == canonical_name)].copy()

    with st.container(border=True):
        st.markdown("##### 💵 Cotações e Médias Móveis")
        bench_options = ["Todos"]
        if not df_p_fert.empty and "benchmark_name" in df_p_fert.columns:
            bench_options += sorted(df_p_fert["benchmark_name"].dropna().unique().tolist())

        c_bench, c_time = st.columns([7, 5])
        with c_bench:
            selected_bench = st.selectbox("Benchmark de Referência:", bench_options, index=0, key=f"sec_price_bench_{slug}")
        with c_time:
            time_window = st.segmented_control("Janela Temporal:", ["1A", "3A", "5A", "Tudo"], default="Tudo", key=f"sec_price_time_{slug}")
            if not time_window:
                time_window = "Tudo"

        filtered_prices = df_p_fert.copy()
        if selected_bench != "Todos":
            filtered_prices = filtered_prices[filtered_prices["benchmark_name"] == selected_bench]

        if not filtered_prices.empty:
            filtered_prices = filtered_prices.sort_values(by="price_date")
            if time_window != "Tudo" and "price_date" in filtered_prices.columns:
                max_date = filtered_prices["price_date"].max()
                years_back = int(time_window.replace("A", ""))
                min_date = max_date - pd.DateOffset(years=years_back)
                filtered_prices = filtered_prices[filtered_prices["price_date"] >= min_date]

        if not filtered_prices.empty:
            latest_row = filtered_prices.iloc[-1]
            latest_price = latest_row["standard_price_usd_per_mt"]
            mom_change = latest_row.get("month_over_month_pct_change")
            moving_avg = latest_row.get("moving_avg_3m_usd")
            hub_name = latest_row.get("hub_port_name", "Global")

            k1, k2, k3 = st.columns(3)
            with k1:
                render_kpi_card(
                    title="Última Cotação Registrada",
                    value=f"$ {latest_price:,.2f} / MT",
                    delta=f"{mom_change:+.2f}% MoM" if pd.notnull(mom_change) else None,
                    delta_positive=(mom_change >= 0) if pd.notnull(mom_change) else None,
                    help_text=f"Hub: {hub_name} (Dólares por Tonelada Métrica)",
                )
            with k2:
                render_kpi_card(
                    title="Média Móvel Trimestral (3M)",
                    value=f"$ {moving_avg:,.2f} / MT" if pd.notnull(moving_avg) else "N/D",
                    delta="Tendência Suavizada",
                    delta_positive=None,
                    help_text="Média dos últimos 3 meses (USD/MT)",
                )
            with k3:
                price_spread = filtered_prices["standard_price_usd_per_mt"].max() - filtered_prices["standard_price_usd_per_mt"].min()
                render_kpi_card(
                    title="Amplitude no Período (Spread)",
                    value=f"$ {price_spread:,.2f} / MT",
                    delta=f"Min: ${filtered_prices['standard_price_usd_per_mt'].min():,.0f} | Max: ${filtered_prices['standard_price_usd_per_mt'].max():,.0f}",
                    delta_positive=None,
                    help_text="Variação máx - mín observada no período",
                )

            fig_line = go.Figure()
            for idx, (b_name, grp) in enumerate(filtered_prices.groupby("benchmark_name")):
                color = FERTI_COLORS[idx % len(FERTI_COLORS)]
                fig_line.add_trace(go.Scatter(
                    x=grp["price_date"],
                    y=grp["standard_price_usd_per_mt"],
                    name=f"{b_name} (Preço)",
                    mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    hovertemplate="<b>%{x|%b %Y}</b><br>Preço: $ %{y:,.2f}/MT<extra></extra>",
                ))
                if "moving_avg_3m_usd" in grp.columns and grp["moving_avg_3m_usd"].notnull().any():
                    fig_line.add_trace(go.Scatter(
                        x=grp["price_date"],
                        y=grp["moving_avg_3m_usd"],
                        name=f"{b_name} (Média 3M)",
                        mode="lines",
                        line=dict(color=color, width=1.5, dash="dot"),
                        opacity=0.6,
                        hovertemplate="<b>%{x|%b %Y}</b><br>Média 3M: $ %{y:,.2f}/MT<extra></extra>",
                    ))

            apply_ferti_theme(fig_line, height=400, x_title="Data da Cotação", y_title="USD por Tonelada Métrica (MT)")
            st.plotly_chart(fig_line, use_container_width=True, config=get_default_plotly_config())

            render_download_csv_button(filtered_prices, filename=f"precos_{slug}.csv")
        else:
            st.info(f"Sem séries de preços para {canonical_name} com os filtros selecionados.")

    st.divider()


def _render_section_brazil(fert: dict[str, Any], slug: str) -> None:
    """Seção 4: Mercado Brasileiro, Consumo Aparente e Dependência com filtros próprios."""
    st.markdown('<div id="mercado-brasileiro"></div>', unsafe_allow_html=True)
    st.markdown("### 🇧🇷 4. Mercado Brasileiro & Dependência Estratégica")
    st.caption("Consumo aparente nacional, importações vs produção interna e dependência de fornecimento externo.")

    canonical_name = fert.get("canonical_name", "Fertilizante")
    df_dep = FertiDataService.get_brazil_external_dependency()

    df_d_fert = pd.DataFrame()
    if not df_dep.empty and "fertilizer_name" in df_dep.columns:
        df_d_fert = df_dep[df_dep["fertilizer_name"].astype(str).str.contains(canonical_name, case=False, na=False) | (df_dep["fertilizer_name"] == canonical_name)].copy()

    with st.container(border=True):
        st.markdown("##### 📦 Balanço Nacional: Produção Interna vs. Importações")
        dep_years = sorted(df_d_fert["ref_year"].dropna().unique().astype(int).tolist(), reverse=True) if not df_d_fert.empty else [2024, 2023, 2022]
        c_by, c_bm = st.columns([6, 6])
        with c_by:
            br_year = st.selectbox("Ano de Referência:", dep_years, index=0, key=f"sec_br_year_{slug}")
        with c_bm:
            br_mode = st.radio("Modo de Exibição:", ["Empilhado", "Lado a Lado"], horizontal=True, key=f"sec_br_mode_{slug}")

        filtered_dep = df_d_fert[df_d_fert["ref_year"] == br_year] if not df_d_fert.empty else pd.DataFrame()

        if not filtered_dep.empty:
            total_imp = filtered_dep["total_imports_mt"].sum()
            total_prod = filtered_dep["national_production_mt"].sum()
            total_exp = filtered_dep["total_exports_mt"].sum()
            apparent_cons = max(0.0, total_prod + total_imp - total_exp)
            dep_rate = (total_imp / apparent_cons * 100) if apparent_cons > 0 else 0.0

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                render_kpi_card(
                    title="Consumo Aparente (BR)",
                    value=format_metric_tons(apparent_cons),
                    delta=f"{canonical_name} ({br_year})",
                    delta_positive=True,
                    help_text="Volume físico total absorvido pelo agro brasileiro",
                )
            with k2:
                render_kpi_card(
                    title="Importações Totais",
                    value=format_metric_tons(total_imp),
                    delta=f"{total_imp/apparent_cons*100:.1f}% da oferta" if apparent_cons > 0 else None,
                    delta_positive=False,
                    help_text="Volume internalizado via portos brasileiros",
                )
            with k3:
                render_kpi_card(
                    title="Produção Nacional",
                    value=format_metric_tons(total_prod),
                    delta=f"{total_prod/apparent_cons*100:.1f}% da oferta" if apparent_cons > 0 else None,
                    delta_positive=True,
                    help_text="Produção da indústria química/mineradora instalada no país",
                )
            with k4:
                render_kpi_card(
                    title="Taxa de Dependência Externa",
                    value=f"{dep_rate:.1f}%",
                    delta="Alerta Estratégico" if dep_rate > 70 else "Nível Equilibrado",
                    delta_positive=False if dep_rate > 70 else True,
                    help_text="Meta PNF (Plano Nacional de Fertilizantes): < 50%",
                )

            fig_bal = px.bar(
                filtered_dep,
                x="fertilizer_name",
                y=["national_production_mt", "total_imports_mt"],
                barmode="stack" if br_mode == "Empilhado" else "group",
                labels={"value": "Volume (MT)", "fertilizer_name": "Produto", "variable": "Tipo de Oferta"},
                color_discrete_map={
                    "national_production_mt": "#10B981",
                    "total_imports_mt": "#3B82F6",
                },
            )
            fig_bal.for_each_trace(lambda t: t.update(
                name="Produção Nacional" if "national_production" in t.name else "Importações"
            ))
            apply_ferti_theme(fig_bal, height=350)
            st.plotly_chart(fig_bal, use_container_width=True, config=get_default_plotly_config())
        else:
            st.info(f"Sem dados de balanço nacional consolidados para {canonical_name} no ano {br_year}.")

    st.divider()


def _render_section_technical_sheet(fert: dict[str, Any]) -> None:
    """Seção 5: Ficha Técnica Completa com Agronomia, Propriedades Físicas, Armazenagem e Tributação."""
    st.markdown('<div id="ficha-tecnica"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 5. Ficha Técnica & Especificações Agronômicas")
    st.caption("Especificações físico-químicas, dinâmicas de solo, compatibilidade e recomendações técnicas.")

    with st.container(border=True):
        col_agron, col_phys = st.columns(2)
        with col_agron:
            st.markdown("##### 🌱 Aplicação Agronômica & Solo")
            usage = fert.get("agronomic_usage", "Especificações agronômicas não cadastradas.")
            st.markdown(f"<p style='line-height:1.6; color:#374151;'>{usage}</p>", unsafe_allow_html=True)

        with col_phys:
            st.markdown("##### 🔬 Propriedades Físico-Químicas")
            phys = fert.get("physical_properties", "Propriedades físicas não cadastradas.")
            st.markdown(f"<p style='line-height:1.6; color:#374151;'>{phys}</p>", unsafe_allow_html=True)

        col_store, col_tax = st.columns(2)
        with col_store:
            st.markdown("##### 📦 Armazenagem, PCUR & Manuseio")
            store = fert.get("handling_storage", "Instruções de manuseio não cadastradas.")
            st.markdown(f"<p style='line-height:1.6; color:#374151;'>{store}</p>", unsafe_allow_html=True)

        with col_tax:
            st.markdown("##### 📑 Nomes Comerciais & Sinônimos")
            synonyms = fert.get("synonyms") or []
            if synonyms:
                st.markdown(" • ".join([f"**{s}**" for s in synonyms]))
            else:
                st.markdown("<p style='color:#9CA3AF;'>Sem sinônimos cadastrados.</p>", unsafe_allow_html=True)

    st.divider()


def render_fertilizer_page(slug_or_id: str | int) -> None:
    """Renderiza a página única alongada de um fertilizante específico."""
    fert = FertiDataService.get_fertilizer_by_slug_or_id(slug_or_id)
    if not fert:
        st.error(f"Fertilizante com identificador '{slug_or_id}' não encontrado no catálogo.")
        return

    canonical_name = fert.get("canonical_name", "Fertilizante")
    slug = fert.get("slug", str(slug_or_id))
    category = fert.get("category_name", "Fertilizante")

    # Header de abertura
    render_header(
        title=f"{canonical_name}",
        subtitle=fert.get("detailed_description", fert.get("description", "Painel analítico completo.")),
        badge_text=category,
        badge_type="emerald",
    )

    # Navegação rápida na sidebar
    _render_sidebar_quick_jump(canonical_name)

    # Destaques de especificações químicas
    _render_hero_specs(fert)

    # Seções sequenciais (página única alongada)
    _render_section_production(fert, slug)
    _render_section_trade(fert, slug)
    _render_section_prices(fert, slug)
    _render_section_brazil(fert, slug)
    _render_section_technical_sheet(fert)

    # Legenda e badges de rodapé
    render_units_legend()
    render_source_badge(f"Perfil Homologado — {canonical_name}", "FertiPartner Analytics")

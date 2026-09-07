"""Visão Analítica e Mercado de Micronutrientes na Agricultura.

Panorama agronômico e de mercado para Zinco (Zn), Boro (B), Cobre (Cu),
Manganês (Mn), Molibdênio (Mo) e Ferro (Fe).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

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
    format_metric_tons,
)


MICRONUTRIENTS_DATA = [
    {
        "element": "Zinco (Zn)",
        "role": "Síntese de triptofano, precursor do AIA (hormônio do crescimento radicular e de gemas).",
        "deficiency_cerrado": "Alta (solos ácidos e arenosos, fixação por fósforo)",
        "sources": "Sulfato de Zinco (20-22% Zn), Óxido de Zinco (75-80% Zn), Quelatos",
        "market_volume_mt": 145000.0,
        "import_share_pct": 82.0,
        "primary_origin": "China, Peru, México",
    },
    {
        "element": "Boro (B)",
        "role": "Germinação do grão de pólen, pegamento de flores, divisão celular e translocação de carboidratos.",
        "deficiency_cerrado": "Crítica em soja, café e algodão sob estresse hídrico",
        "sources": "Ácido Bórico (17% B), Octaborato de Sódio (20.5% B), Ulexita (10% B)",
        "market_volume_mt": 110000.0,
        "import_share_pct": 94.0,
        "primary_origin": "Turquia, Estados Unidos, Chile",
    },
    {
        "element": "Cobre (Cu)",
        "role": "Ativador enzimático na fotossíntese, síntese de lignina e resistência mecânica celular.",
        "deficiency_cerrado": "Frequente em solos com alto teor de matéria orgânica ou solos arenosos",
        "sources": "Sulfato de Cobre (25% Cu), Óxido Cuproso, Quelatos EDTA",
        "market_volume_mt": 48000.0,
        "import_share_pct": 78.0,
        "primary_origin": "Chile, Peru, Alemanha",
    },
    {
        "element": "Manganês (Mn)",
        "role": "Fotólise da água no fotossistema II, respiração celular e metabolismo do nitrogênio.",
        "deficiency_cerrado": "Induzida por excesso de calagem (pH > 6.2) e glifosato",
        "sources": "Sulfato de Manganês (28-31% Mn), Óxido de Manganês, Quelatos",
        "market_volume_mt": 85000.0,
        "import_share_pct": 45.0,
        "primary_origin": "Brasil (Nacional), África do Sul, Gabão",
    },
    {
        "element": "Molibdênio (Mo)",
        "role": "Componente chave das enzimas nitrogenase e redutase do nitrato; indispensável para FBN em soja.",
        "deficiency_cerrado": "Geralmente corrigido via tratamento de sementes e pulverização foliar",
        "sources": "Molibdato de Sódio (39% Mo), Molibdato de Amônio (54% Mo)",
        "market_volume_mt": 4200.0,
        "import_share_pct": 98.0,
        "primary_origin": "China, Chile, Estados Unidos",
    },
    {
        "element": "Cobalto (Co)",
        "role": "Coenzima da vitamina B12 nos bacteroides dos nódulos radiculares na fixação biológica de N2.",
        "deficiency_cerrado": "Essencial em doses mínimas (gramas/ha) associado ao Molibdênio",
        "sources": "Sulfato de Cobalto (21% Co), Cloreto de Cobalto",
        "market_volume_mt": 1800.0,
        "import_share_pct": 99.0,
        "primary_origin": "República Democrática do Congo, Finlândia, Canadá",
    },
]


def render_micronutrients_page() -> None:
    """Renderiza a página única do panorama de Micronutrientes."""
    render_header(
        title="Micronutrientes na Agricultura",
        subtitle="Mapeamento agronômico, demanda de mercado e balanço de suprimento para Zinco, Boro, Cobre, Manganês, Molibdênio e Cobalto.",
        badge_text="Micronutrientes",
        badge_type="purple",
    )

    with st.sidebar:
        st.markdown("#### 🧭 Navegação — Micronutrientes")
        st.markdown(
            """
            <div style="font-size: 0.88rem; line-height: 1.8;">
                <a href="#kpis-micro" style="text-decoration: none; color: #1B4332; font-weight: 600;">📊 1. Indicadores do Mercado</a><br>
                <a href="#demanda-micro" style="text-decoration: none; color: #1B4332; font-weight: 600;">🌾 2. Demanda por Elemento</a><br>
                <a href="#origens-micro" style="text-decoration: none; color: #1B4332; font-weight: 600;">🚢 3. Dependência Externa & Origens</a><br>
                <a href="#especificacoes-micro" style="text-decoration: none; color: #1B4332; font-weight: 600;">📋 4. Especificações Técnicas</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

    df_micro = pd.DataFrame(MICRONUTRIENTS_DATA)

    st.markdown('<div id="kpis-micro"></div>', unsafe_allow_html=True)
    st.markdown("### 📊 1. Indicadores Globais e Nacionais de Micronutrientes")

    total_demand = df_micro["market_volume_mt"].sum()
    weighted_import_dep = (df_micro["market_volume_mt"] * df_micro["import_share_pct"]).sum() / total_demand

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card(
            title="Consumo Anual Estimado (BR)",
            value=f"{total_demand / 1000:,.1f} k MT",
            delta="Insumos Especiais",
            delta_positive=True,
            help_text="Volume físico total de matérias-primas e sais de micronutrientes consumidos",
        )
    with c2:
        render_kpi_card(
            title="Dependência Externa Ponderada",
            value=f"{weighted_import_dep:.1f}%",
            delta="Vulnerabilidade Crítica",
            delta_positive=False,
            help_text="Percentual médio importado ponderado pelo volume de cada micronutriente",
        )
    with c3:
        render_kpi_card(
            title="Elementos Homologados",
            value="6 Elementos",
            delta="Zn, B, Cu, Mn, Mo, Co",
            delta_positive=True,
            help_text="Nutrientes de alta resposta agronômica no Cerrado e biomas agrícolas",
        )

    st.divider()

    st.markdown('<div id="demanda-micro"></div>', unsafe_allow_html=True)
    st.markdown("### 🌾 2. Demanda de Mercado por Micronutriente (Toneladas Métricas)")

    col_chart, col_dep = st.columns([7, 5])
    with col_chart:
        fig_vol = px.bar(
            df_micro.sort_values(by="market_volume_mt", ascending=True),
            x="market_volume_mt",
            y="element",
            orientation="h",
            labels={"market_volume_mt": "Volume de Demanda (MT)", "element": "Elemento"},
            color="market_volume_mt",
            color_continuous_scale="Viridis",
        )
        fig_vol.update_traces(texttemplate="%{x:,.0f} MT", textposition="inside")
        apply_ferti_theme(fig_vol, height=360, show_legend=False)
        st.plotly_chart(fig_vol, width="stretch", config=get_default_plotly_config())

    with col_dep:
        fig_dep = px.bar(
            df_micro.sort_values(by="import_share_pct", ascending=True),
            x="import_share_pct",
            y="element",
            orientation="h",
            labels={"import_share_pct": "Taxa de Importação (%)", "element": "Elemento"},
            color="import_share_pct",
            color_continuous_scale="Reds",
        )
        fig_dep.update_traces(texttemplate="%{x:.1f}%", textposition="inside")
        apply_ferti_theme(fig_dep, height=360, show_legend=False)
        st.plotly_chart(fig_dep, width="stretch", config=get_default_plotly_config())

    st.divider()

    st.markdown('<div id="origens-micro"></div>', unsafe_allow_html=True)
    st.markdown("### 🚢 3. Principais Origens e Fontes Minerais")
    with st.container(border=True):
        st.dataframe(
            df_micro[["element", "sources", "import_share_pct", "primary_origin"]].rename(columns={
                "element": "Micronutriente",
                "sources": "Principais Fontes e Sais Comerciais",
                "import_share_pct": "Dependência de Importação (%)",
                "primary_origin": "Maiores Polos Globais de Fornecimento",
            }),
            column_config={
                "Dependência de Importação (%)": st.column_config.ProgressColumn(
                    "Importação (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            width="stretch",
            hide_index=True,
        )
        render_download_csv_button(df_micro, filename="micronutrientes_mercado.csv")

    st.divider()

    st.markdown('<div id="especificacoes-micro"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 4. Especificações e Dinâmica Agronômica")
    for item in MICRONUTRIENTS_DATA:
        with st.expander(f"🔬 {item['element']} — Ficha Técnica & Aplicação", expanded=False):
            st.markdown(f"**Função Fisiológica na Planta:** {item['role']}")
            st.markdown(f"**Diagnóstico no Solo (Cerrado/Brasil):** {item['deficiency_cerrado']}")
            st.markdown(f"**Fontes Químicas Utilizadas:** {item['sources']}")
            st.markdown(f"**Origem do Suprimento Internacional:** {item['primary_origin']}")

    st.divider()
    render_units_legend()
    render_source_badge("Panorama de Micronutrientes", "FertiPartner Agronomia")


def render_page() -> None:
    render_micronutrients_page()


if __name__ == "__main__":
    render_page()

"""Status das Fontes, Auditoria e Observabilidade Operacional."""

import streamlit as st
import pandas as pd

from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
    render_download_csv_button,
)


def render_view() -> None:
    render_header(
        title="Observabilidade & Fontes de Dados",
        subtitle="Monitoramento operacional das rotinas de ingestão de dados, integridade dos pipelines e auditoria de fontes oficiais.",
        badge_text="Observabilidade",
        badge_type="emerald",
    )

    is_connected = FertiDataService.check_connection()
    df_runs = FertiDataService.get_audit_runs()
    df_sources = FertiDataService.get_sources_status()

    # Controles superiores
    c_btn, _ = st.columns([3, 9])
    with c_btn:
        if st.button("🔄 Atualizar Métricas & Limpar Cache", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card(
            title="Conexão Supabase / PostgreSQL",
            value="Operacional" if is_connected else "Modo Resiliente",
            delta="Online (Segurança RLS)" if is_connected else "Modo Resiliente",
            delta_positive=True if is_connected else False,
            help_text="Banco de dados em nuvem",
        )
    with c2:
        active_sources = len(df_sources) if not df_sources.empty else 4
        render_kpi_card(
            title="Fontes Integradas Ativas",
            value=f"{active_sources} Provedores",
            delta="MDIC • Comtrade • FAO • FRED",
            delta_positive=True,
            help_text="Pipelines com retentativa e backoff",
        )
    with c3:
        total_runs = len(df_runs) if not df_runs.empty else 0
        render_kpi_card(
            title="Rotinas de Ingestão Monitoradas",
            value=f"{total_runs} Execuções",
            delta="Auditoria Contínua",
            delta_positive=True,
            help_text="Logs em data_collection_runs",
        )

    st.divider()

    tab_runs, tab_sources, tab_consistency, tab_sla = st.tabs([
        "Histórico de Coletas & Ingestões",
        "Fontes de Dados Mapeadas",
        "Matriz de Consistência Temporal",
        "Políticas Operacionais & SLAs",
    ])

    with tab_runs:
        st.markdown("##### Execuções Recentes do Pipeline de Dados")
        st.caption("Histórico detalhado de cada rotina disparada, com os parâmetros/escopos requisitados e tempo de execução.")
        if not df_runs.empty:
            cols_show = ["source_name", "requested_data", "status", "records_count", "records_fetched", "started_at", "execution_time_sec"]
            existing_cols = [c for c in cols_show if c in df_runs.columns]
            df_display = df_runs[existing_cols].copy()

            # Formatar timestamp de início
            if "started_at" in df_display.columns:
                df_display["started_at"] = pd.to_datetime(df_display["started_at"]).dt.strftime("%d/%m/%Y %H:%M:%S")

            st.dataframe(
                df_display.rename(columns={
                    "source_name": "Fonte Provedora",
                    "requested_data": "Dado Requisitado / Escopo",
                    "status": "Status",
                    "records_count": "Inseridos",
                    "records_fetched": "Obtidos",
                    "started_at": "Horário Início",
                    "execution_time_sec": "Duração (s)",
                }),
                column_config={
                    "Inseridos": st.column_config.NumberColumn(format="%d"),
                    "Obtidos": st.column_config.NumberColumn(format="%d"),
                    "Duração (s)": st.column_config.NumberColumn(format="%.1f s"),
                },
                width="stretch",
                hide_index=True,
            )
            render_download_csv_button(df_runs, filename="historico_ingestoes_fertipartner.csv")
        else:
            st.info("Nenhum log de execução encontrado.")

    with tab_sources:
        st.markdown("##### Fontes Oficiais Estruturadas no Ecossistema")
        st.caption("Data e hora da última ingestão bem-sucedida e parâmetros requisitados de cada conector externo.")
        if not df_sources.empty:
            df_src_display = df_sources.copy()
            if "last_ingestion" in df_src_display.columns:
                def format_ts(val):
                    if not val or val == "Pendente de execução":
                        return "Pendente de execução"
                    try:
                        return pd.to_datetime(val).strftime("%d/%m/%Y %H:%M:%S")
                    except Exception:
                        return str(val)
                df_src_display["last_ingestion"] = df_src_display["last_ingestion"].apply(format_ts)

            st.dataframe(
                df_src_display.rename(columns={
                    "source_name": "Provedor / API",
                    "source_code": "Código",
                    "frequency": "Frequência",
                    "last_ingestion": "Última Ingestão",
                    "last_status": "Último Status",
                    "records_inserted": "Registros Ingeridos",
                    "requested_data": "Último Dado Requisitado",
                }),
                column_config={
                    "Registros Ingeridos": st.column_config.NumberColumn(format="%d"),
                },
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Nenhuma fonte cadastrada.")

    with tab_consistency:
        st.markdown("##### Auditoria de Consistência & Assimetria Temporal")
        st.caption("Monitoramento do pareamento entre fontes com calendários de divulgação distintos (Comércio Aduaneiro vs Censo de Produção vs Séries de Preços).")

        df_matrix = FertiDataService.get_database_consistency_matrix()
        if not df_matrix.empty:
            # Cards de resumo
            c_c1, c_c2, c_c3 = st.columns(3)
            with c_c1:
                synced_count = (df_matrix["synchronization_status"] == "FULLY_SYNCHRONIZED").sum()
                st.metric("Pares Totalmente Sincronizados", f"{synced_count} Séries", "Trade + Produção + Preço")
            with c_c2:
                pending_prod = (df_matrix["synchronization_status"] == "AWAITING_PRODUCTION_SURVEY").sum()
                st.metric("Aguardando Censo Produção", f"{pending_prod} Séries", "Defasagem típica de 1-2 anos")
            with c_c3:
                pending_trade = (df_matrix["synchronization_status"] == "AWAITING_TRADE_DATA").sum()
                st.metric("Aguardando Comércio Exterior", f"{pending_trade} Séries", "Atualização aduaneira pendente")

            st.write("")
            status_labels = {
                "FULLY_SYNCHRONIZED": "Totalmente Sincronizado",
                "AWAITING_PRODUCTION_SURVEY": "Aguardando Censo Produção (FAO/IFA)",
                "AWAITING_TRADE_DATA": "Aguardando Aduana (Comex/Comtrade)",
                "PARTIAL_DATA": "Parcial / Histórico",
            }
            df_m_disp = df_matrix.copy()
            if "synchronization_status" in df_m_disp.columns:
                df_m_disp["Status Integridade"] = df_m_disp["synchronization_status"].map(status_labels).fillna(df_m_disp["synchronization_status"])

            st.dataframe(
                df_m_disp.rename(columns={
                    "ref_year": "Ano Ref.",
                    "fertilizer_name": "Fertilizante",
                    "trade_records_count": "Fluxos Comércio",
                    "prod_records_count": "Registros Produção",
                    "producing_countries_count": "Países Produtores",
                    "price_points_count": "Pontos de Preço",
                })[["Ano Ref.", "Fertilizante", "Fluxos Comércio", "Registros Produção", "Países Produtores", "Pontos de Preço", "Status Integridade"]],
                width="stretch",
                hide_index=True,
            )
            render_download_csv_button(df_matrix, filename="matriz_consistencia_banco_dados.csv")
        else:
            st.info("Matriz de consistência não disponível.")

    with tab_sla:
        st.markdown("##### Políticas de Coleta & SLAs Operacionais")
        st.markdown(
            """
            - **MDIC Comex Stat**: Atualização mensal até o 10º dia útil de cada mês com dados consolidados da balança comercial brasileira.
            - **UN Comtrade**: Atualização mensal das matrizes bilaterais globais para fluxos de importação e exportação.
            - **FAOSTAT / IFA**: Sincronização anual de dados consolidados de capacidade industrial e balanço aparente de safras.
            - **FRED / Banco Mundial**: Séries históricas de benchmarks internacionais (Ureia Black Sea, MAP US Gulf, KCl Vancouver).
            - **Google News RSS Feed**: Captura contínua de publicações setoriais com janela temporal estrita de 7 dias (168 horas).
            
            Para consultar a arquitetura completa do sistema, modelagem 4NF e especificações técnicas de código, acesse a página **Software** no menu lateral.
            """
        )

    st.divider()
    render_source_badge("Logs de Execução & Auditoria FertiPartner", "Tempo Real")


if __name__ == "__main__":
    render_view()

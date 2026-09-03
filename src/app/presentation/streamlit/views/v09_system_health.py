"""Status das Fontes, Auditoria e Saúde da Arquitetura 4NF (RF17, RF19, RF20)."""

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
        title="Auditoria, Fontes & Infraestrutura 4NF",
        subtitle="Monitoramento das rotinas de ingestão de dados, integridade dos pipelines, auditoria SHA-256 e conformidade da modelagem em Quarta Forma Normal.",
        badge_text="System Health",
        badge_type="emerald",
    )

    is_connected = FertiDataService.check_connection()
    df_runs = FertiDataService.get_audit_runs()

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card(
            title="Conexão Supabase / PostgreSQL",
            value="Operacional" if is_connected else "Fallback / Local",
            delta="Online (RLS Ativo)" if is_connected else "Modo Resiliente",
            delta_positive=True if is_connected else False,
            help_text="Banco de dados em nuvem 4NF",
        )
    with c2:
        render_kpi_card(
            title="Fontes Integradas Ativas",
            value="4 Provedores",
            delta="MDIC • Comtrade • FAO • FRED",
            delta_positive=True,
            help_text="Pipelines com retentativa e backoff",
        )
    with c3:
        total_runs = len(df_runs) if not df_runs.empty else 0
        render_kpi_card(
            title="Rotinas de Ingestão Monitoradas",
            value=f"{total_runs} Execuções",
            delta="Auditoria Contínua (RNF02)",
            delta_positive=True,
            help_text="Logs em data_collection_runs",
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    tab_runs, tab_sources, tab_arch = st.tabs([
        "⏱️ Histórico de Coletas & Ingestões",
        "📡 Fontes de Dados Mapeadas",
        "🛡️ Arquitetura 4NF & Garantias Técnicas",
    ])

    with tab_runs:
        st.markdown("##### 📜 Execuções Recentes do Pipeline de Dados")
        if not df_runs.empty:
            st.dataframe(
                df_runs.rename(columns={
                    "source_name": "Fonte Provedora",
                    "source_code": "Código",
                    "status": "Status",
                    "records_count": "Registros Ingeridos",
                    "started_at": "Horário Início",
                    "execution_time_sec": "Duração (s)",
                }),
                column_config={
                    "Registros Ingeridos": st.column_config.NumberColumn(format="%d"),
                    "Duração (s)": st.column_config.NumberColumn(format="%.2f s"),
                },
                use_container_width=True,
                hide_index=True,
            )
            render_download_csv_button(df_runs, filename="auditoria_coletas.csv")
        else:
            st.info("Nenhum log de execução encontrado.")

    with tab_sources:
        st.markdown("##### 🌐 Fontes Oficiais Estruturadas no Ecossistema")
        sources_data = [
            {"Provedor": "MDIC Comex Stat", "Frequência": "Mensal", "Abrangência": "Microdados aduaneiros do Brasil (NCM, UF, País)", "Status": "Ativo"},
            {"Provedor": "UN Comtrade", "Frequência": "Mensal", "Abrangência": "Comércio exterior bilateral global (códigos SH)", "Status": "Ativo"},
            {"Provedor": "FAOSTAT (FAO)", "Frequência": "Anual", "Abrangência": "Balanço nutricional mundial, produção e consumo", "Status": "Ativo"},
            {"Provedor": "FRED (Federal Reserve)", "Frequência": "Mensal", "Abrangência": "Séries históricas de preços internacionais e índices PPI", "Status": "Ativo"},
        ]
        st.dataframe(pd.DataFrame(sources_data), use_container_width=True, hide_index=True)

    with tab_arch:
        st.markdown("##### 🏗️ Garantias de Arquitetura em Quarta Forma Normal (4NF)")
        st.markdown(
            """
            - **Eliminação de Dependências Multivaloradas**: Todas as tabelas de fatos (`trade_records`, `production_records`, `price_records`, `brazil_trade_details`) isolam estritamente cada dimensão de negócio.
            - **Idempotência e Auditoria Completa (RNF02)**: O repositório `raw_data` armazena os payloads brutos integrais com chave de verificação criptográfica SHA-256 (`payload_hash`), prevenindo duplicações e garantindo auditoria forense.
            - **Segurança Nativa via Row Level Security (RLS)**: Políticas ativas para leitura pública (`anon`, `authenticated`) e restrição de escrita apenas para `service_role`.
            - **Controle de Resiliência de Requisições HTTP**: Rate limiting dedicado por provedor com estratégia de *exponential backoff* e *jitter* contra HTTP 429.
            """
        )

    render_source_badge("Logs de Execução & Auditoria FertiPartner", "Tempo Real")


if __name__ == "__main__" or "render_view" in globals():
    render_view()

"""View de Engenharia e Arquitetura de Software do FertiPartner."""

import streamlit as st

from app.presentation.streamlit.components.ui import (
    render_header,
    render_kpi_card,
    render_source_badge,
)


def render_view() -> None:
    """Renderiza a documentação técnica e arquitetural da plataforma FertiPartner."""
    render_header(
        title="Engenharia & Arquitetura de Software",
        subtitle="Especificações técnicas, decisões de design arquitetural, modelagem de dados 4NF e padrões de engenharia implementados no FertiPartner.",
        badge_text="Arquitetura & Engenharia",
        badge_type="emerald",
    )

    # Métricas Técnicas de Alto Nível
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            title="Padrão Arquitetural",
            value="Clean Architecture",
            delta="4 Camadas Isoladas",
            delta_positive=True,
            help_text="Domain, Application, Infrastructure, Presentation",
        )
    with c2:
        render_kpi_card(
            title="Modelagem Relacional",
            value="Quarta Forma Normal (4NF)",
            delta="Segurança RLS Ativa",
            delta_positive=True,
            help_text="Zero anomalias de atualização e tabelas atômicas",
        )
    with c3:
        render_kpi_card(
            title="Cobertura de Testes (TDD)",
            value="161 Testes Unitários",
            delta="100% Taxa de Sucesso",
            delta_positive=True,
            help_text="Suíte de testes automatizados via Pytest",
        )
    with c4:
        render_kpi_card(
            title="Motor Cognitivo de IA",
            value="Gemini 3.x Flash",
            delta="RAG + Function Calling",
            delta_positive=True,
            help_text="Execução determinística de tools com Thought Signature",
        )

    st.write("")

    # Abas estruturadas de aprofundamento técnico
    tab_arch, tab_data, tab_ai, tab_quality = st.tabs([
        "Clean Architecture",
        "Modelagem de Dados 4NF",
        "Engenharia de IA (FertiPartner.AI)",
        "Resiliência & Qualidade de Código",
    ])

    with tab_arch:
        st.markdown("#### Padrão Arquitetural: Clean Architecture")
        st.markdown(
            """
            O FertiPartner foi desenvolvido estritamente sobre os preceitos da **Clean Architecture** (Arquitetura Limpa),
            garantindo que as regras de negócio permaneçam desacopladas de bibliotecas de terceiros, frameworks de interface
            e tecnologias de banco de dados.
            """
        )

        col_dom, col_app = st.columns(2)
        with col_dom:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; height: 100%;">
                    <div style="font-weight: 700; color: #1B4332; font-size: 1rem; margin-bottom: 0.5rem;">
                        1. Camada de Domínio (src/app/domain/)
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        Contém as entidades de negócio puras, enums agronômicos e contratos de ferramentas analíticas.
                        Não possui qualquer dependência externa ou conhecimento sobre banco de dados e APIs.
                        <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                            <li><b>Entidades:</b> Fertilizer, PriceRecord, TradeFlowRecord, ChatMessage.</li>
                            <li><b>Enums:</b> NutrientType, ApplicationRole, SyncStatus.</li>
                            <li><b>Contratos de Tools:</b> Declaração estrita de esquemas para Function Calling.</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_app:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; height: 100%;">
                    <div style="font-weight: 700; color: #1B4332; font-size: 1rem; margin-bottom: 0.5rem;">
                        2. Camada de Aplicação (src/app/application/)
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        Implementa os casos de uso do sistema e orquestra a execução das regras de negócio com o auxílio das abstrações de infraestrutura.
                        <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                            <li><b>CopilotOrchestrator:</b> Coordena diálogos em múltiplos turnos e roteamento de ferramentas.</li>
                            <li><b>ToolExecutor:</b> Executa consultas especializadas em dados tabulares com tratamento de exceções.</li>
                            <li><b>ExecutiveBriefingUseCase:</b> Síntese automatizada de conjuntura macroeconômica e preços.</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        col_infra, col_pres = st.columns(2)
        with col_infra:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; height: 100%;">
                    <div style="font-weight: 700; color: #1B4332; font-size: 1rem; margin-bottom: 0.5rem;">
                        3. Camada de Infraestrutura (src/app/infrastructure/)
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        Concretiza integrações com provedores externos, gateways de rede e persistência de dados.
                        <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                            <li><b>PostgREST / Supabase Client:</b> Acesso relacional a tabelas normalizadas via HTTPS.</li>
                            <li><b>HTTP Resilient Client:</b> Conexões com retentativas exponenciais, full-jitter e circuit breaking.</li>
                            <li><b>Gemini Client:</b> Integração com a API Google Gemini 3.x, suporte a streaming e injeção de thought signatures.</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_pres:
            st.markdown(
                """
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; height: 100%;">
                    <div style="font-weight: 700; color: #1B4332; font-size: 1rem; margin-bottom: 0.5rem;">
                        4. Camada de Apresentação (src/app/presentation/)
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                        Responsável pela interface do usuário e experiência analítica, sem abrigar regras de negócio.
                        <ul style="margin-top: 0.5rem; padding-left: 1.2rem;">
                            <li><b>Streamlit Modular Views:</b> Vistas isoladas (v01 a v12) com responsabilidade única de renderização.</li>
                            <li><b>Services Singletons:</b> Caching inteligente (st.cache_data) e gateways de estado de sessão.</li>
                            <li><b>Design System Atômico:</b> Componentes visuais padronizados (render_header, render_kpi_card).</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        st.markdown("##### Regras de Dependência Unidirecional")
        st.markdown(
            """
            ```
            ┌─────────────────────────────────────────────────────────┐
            │             Presentation (Streamlit UI & Services)      │
            └───────────────────────────┬─────────────────────────────┘
                                        │ chama
                                        ▼
            ┌─────────────────────────────────────────────────────────┐
            │             Application (Use Cases & Orchestrators)     │
            └───────────────┬─────────────────────────┬───────────────┘
                            │ coordena                │ utiliza
                            ▼                         ▼
            ┌───────────────────────────┐ ┌───────────────────────────┐
            │ Domain (Entidades/Regras) │ │ Infrastructure (APIs/BD)  │
            └───────────────────────────┘ └───────────────────────────┘
            ```
            - **Domain** não importa nenhuma outra camada.
            - **Application** importa apenas Domain e interfaces de Infrastructure.
            - **Presentation** consome Application e componentes de UI, nunca manipulando conexões de banco de dados diretamente.
            """
        )

    with tab_data:
        st.markdown("#### Modelagem de Dados Relacional em Quarta Forma Normal (4NF)")
        st.markdown(
            """
            Para eliminar completamente anomalias de inserção, atualização e exclusão em dados complexos de séries temporais agrícolas,
            o banco de dados PostgreSQL foi estruturado sob os princípios da **4NF (Quarta Forma Normal)**.
            """
        )

        st.markdown(
            """
            - **1NF (Primeira Forma Normal):** Todos os atributos são estritamente atômicos. Não há arrays desnormalizados ou campos concatenados nas tabelas de fatos.
            - **2NF (Segunda Forma Normal):** Todos os atributos não-chave dependem funcionalmente da totalidade da chave primária composta (e não apenas de parte dela).
            - **3NF (Terceira Forma Normal):** Ausência total de dependências transitivas entre colunas não-chave.
            - **4NF (Quarta Forma Normal):** Eliminação de dependências multivaloradas independentes. Dimensões como tempo, país, produto e modalidade comercial são separadas em entidades próprias.
            """
        )

        st.write("")
        st.markdown("##### Esquema de Tabelas de Fatos & Dimensões")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown(
                """
                **Tabelas de Fatos Atômicas:**
                - `fertilizer_prices`: Registros temporais de cotações mensais por produto, praça e porto de entrega.
                - `trade_flows`: Matriz bilateral de comércio exterior (exportador, importador, NCM, volume em toneladas e valor FOB/CIF em USD).
                - `production_volumes`: Volumes de síntese industrial por país, ano e fertilizante base.
                - `apparent_consumption`: Balanço aparente nacional (Produção + Importações - Exportações).
                """
            )
        with col_t2:
            st.markdown(
                """
                **Tabelas de Dimensões & Governança:**
                - `fertilizers`: Nomenclatura oficial, fórmula química, concentração N-P-K e grupo agronômico.
                - `countries`: Código ISO-3, blocos econômicos e nomes padronizados em português e inglês.
                - `states_brazil`: Unidades Federativas, regiões macroeconômicas e polos agropecuários.
                - `data_collection_runs`: Logs de auditoria contínua de ingestão com hash SHA-256 de carga.
                """
            )

        st.write("")
        st.markdown("##### Idempotência e Segurança de Dados")
        st.markdown(
            """
            - **Idempotência por Hash SHA-256:** Cada lote de dados coletado via pipeline recebe um cálculo criptográfico de integridade (`payload_hash`). O banco rejeita duplicatas idênticas em caso de reexecução de tarefas agendadas.
            - **Row Level Security (RLS):** As políticas de segurança no PostgreSQL garantem que usuários anônimos e aplicações de apresentação tenham permissão estritamente restrita de leitura (`SELECT`), enquanto escritas (`INSERT/UPDATE`) exigem tokens de serviço autenticados.
            """
        )

    with tab_ai:
        st.markdown("#### Engenharia do Assistente FertiPartner.AI")
        st.markdown(
            """
            O FertiPartner.AI utiliza uma abordagem híbrida de **RAG Quantitativo (Retrieval-Augmented Generation) com Function Calling Determinístico**.
            Modelos de linguagem puros costumam sofrer com alucinações numéricas e imprecisões em séries temporais. Para sanar essa vulnerabilidade,
            o assistente atua como um agente orquestrador que consulta as tabelas relacionais do sistema em tempo de inferência.
            """
        )

        st.markdown("##### Ferramentas de Domínio Disponíveis para o Agente (Tools)")
        st.markdown(
            """
            1. `get_fertilizer_prices`: Recupera séries históricas e cotações recentes de fertilizantes por porto ou benchmark internacional.
            2. `get_trade_flows`: Consulta fluxos bilaterais de importação e exportação (origem, destino, tonelagem e valor financeiro).
            3. `get_production_rankings`: Obtém o ranking global de capacidade produtiva industrial e market share internacional.
            4. `get_market_sentiment_barometers`: Avalia o sentimento setorial ponderado das últimas 168 horas por macronutriente.
            5. `get_market_news`: Busca notícias recentes com filtro de busca e janela temporal rigorosa de 7 dias.
            6. `get_fertilizer_details`: Retorna ficha técnica completa, características agronômicas e concentração de nutrientes.
            """
        )

        st.write("")
        st.markdown("##### Compatibilidade com Google Gemini 3.x & Injeção de Thought Signature")
        st.markdown(
            """
            Para garantir compatibilidade com as especificações da família **Google Gemini 3.x Flash**, a camada de infraestrutura de IA implementa:
            - **Preservação de `thoughtSignature`:** O modelo Gemini 3.x exige a presença da assinatura de pensamento em chamadas intermediárias de ferramentas. A infraestrutura do FertiPartner preserva e reinjeta automaticamente essa assinatura nas respostas enviadas pelo `ToolExecutor`.
            - **Parâmetro `thinkingLevel: LOW`:** Em tarefas de chat analítico direto com chamadas de ferramentas, a profundidade excessiva de reflexão pode introduzir tempos de espera de até 60 segundos. A configuração otimizada de reflexão leve reduz a latência para menos de 4 segundos sem perda de rigor analítico.
            - **Retentativa Inteligente contra HTTP 503 (High Demand):** Durante picos temporários de carga nos servidores do Google Gemini, o cliente executa até 3 tentativas com recuo exponencial e ruído estocástico (jitter), mitigando falhas efêmeras de disponibilidade.
            """
        )

        st.write("")
        st.markdown("##### Arquitetura de GuardRails & Segurança de IA (AIGuardrails)")
        st.markdown(
            """
            Para mitigar vulnerabilidades clássicas de modelos de linguagem e garantir rigor corporativo, a camada de domínio implementa o componente **`AIGuardrails`** (`src/app/domain/ai/guardrails.py`):
            - **Defesa Pré-Inferência contra Prompt Injection & Jailbreak:** Cada mensagem submetida pelo usuário passa por uma esteira determinística de análise léxica e regex. Padrões de ataque como tentativas de override (*"ignore all previous instructions"*, *"now you are DAN"*, *"modo desenvolvedor"*), injeções de papéis falsos (`<system>`, `[SYSTEM]`) e comandos de código malicioso são interceptados e bloqueados antes mesmo do envio da requisição ao Gemini, economizando cotas de API e blindando a aplicação.
            - **Contenção Estrita de Escopo de Domínio (Domain Bounding):** O assistente foi concebido estritamente para o ecossistema de fertilizantes e mercado agropecuário. O motor de guardrails avalia a pertinência temática do prompt (fertilizantes, nutrientes, dinâmica de solos, cotações, portos, safras e comércio internacional). Consultas alheias a esse escopo (culinária, esportes, programação genérica, ficção) recebem uma recusa cortês e institucional, redirecionando o usuário para os recursos agronômicos da plataforma.
            - **Proteção contra Exfiltração de System Prompt:** Bloqueio ativo de tentativas de extração de diretrizes internas, system prompts ou chaves do ambiente.
            - **Reforço de Prompt no Nível do Sistema:** O `SYSTEM_PROMPT_FERTIPARTNER_AI` contém cláusulas mandatórias de não-conformidade com instruções do usuário que atentem contra as políticas de segurança e a seriedade executiva do FertiPartner.
            """
        )

    with tab_quality:
        st.markdown("#### Qualidade de Código, Resiliência & TDD")
        st.markdown(
            """
            O projeto segue padrões industriais de engenharia de software para assegurar estabilidade contínua:
            """
        )

        st.markdown(
            """
            - **Desenvolvimento Orientado a Testes (TDD):** Todos os casos de uso, parsers de fontes externas e componentes visuais contam com testes automatizados executados via Pytest. A suíte é verificada antes de qualquer alteração integrada ao repositório.
            - **Cliente HTTP Resiliente:** Conexões externas utilizam estratégias de retentativa exponencial com jitter aleatório para prevenir sobrecarga de serviços terceiros e falhas por timeouts transitórios.
            - **Tipagem Estática & Data Classes:** O código adota anotações estritas de tipo (`typing`), validadores de formato e estruturas de dados imutáveis onde aplicável.
            - **Isolamento de Estado no Streamlit:** O estado da aplicação (`st.session_state` e `st.cache_data`) é segregado por responsabilidades, prevenindo vazamento de dados entre abas ou chamadas concorrentes.
            """
        )

    st.divider()
    render_source_badge("Especificações de Engenharia de Software FertiPartner", "Clean Architecture")


if __name__ == "__main__":
    render_view()

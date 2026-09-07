"""View principal da página dedicada do FertiPartner.AI."""

import streamlit as st

from app.domain.ai.entities import ChatMessage, ChatRole
from app.presentation.streamlit.components.ui import render_header, render_source_badge
from app.presentation.streamlit.services.ai_service import FertiAIService


def render_view() -> None:
    """Renderiza a interface de chat analítico do FertiPartner.AI."""
    render_header(
        title="FertiPartner.AI - Inteligência Analítica de Mercado",
        subtitle="Assistente especialista com RAG Híbrido e Function Calling integrado diretamente às cotações históricas, balanço físico nacional, rotas do UN Comtrade e notícias em tempo real.",
        badge_text="Powered by Google Gemini",
        badge_type="emerald",
    )

    api_key = FertiAIService.get_api_key()

    # Se não houver chave configurada, bloqueia os recursos de IA e exibe a tela de configuração
    if not api_key:
        FertiAIService.render_api_key_setup_card()
        st.divider()
        render_source_badge("Google Gemini AI Studio API & FertiPartner Data Layer", "RAG Híbrido")
        return

    # Inicializa histórico na sessão
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Barra superior de controle e status
    c_status, c_model, c_clear, c_disconnect = st.columns([3, 2.5, 1.5, 1.5])
    with c_status:
        st.markdown(
            """
            <div style="font-size: 0.82rem; color: #2D6A4F; font-weight: 600; padding: 0.4rem 0;">
                Status: <b>Ativo & Conectado</b> (Bancos 4NF + Feed 7d)
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_model:
        available_models = FertiAIService.get_available_models()
        curr_model = FertiAIService.get_selected_model()
        if curr_model not in available_models:
            curr_model = available_models[0]
            FertiAIService.set_selected_model(curr_model)

        sel_model = st.selectbox(
            "Modelo Gemini:",
            available_models,
            index=available_models.index(curr_model) if curr_model in available_models else 0,
            key="sb_select_gemini_model",
            label_visibility="collapsed",
        )
        if sel_model != curr_model:
            FertiAIService.set_selected_model(sel_model)
            st.rerun()

    with c_clear:
        if st.button("Limpar Chat", width="stretch"):
            st.session_state.ai_chat_history = []
            st.rerun()

    with c_disconnect:
        if st.button("Desconectar", width="stretch"):
            FertiAIService.clear_api_key()
            st.rerun()

    # Sugestões Rápidas de Perguntas (Quick Prompts)
    st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: #4B5563; margin-top: 0.5rem; margin-bottom: 0.35rem;'>Sugestões de Análises Rápidas:</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)

    prompt_to_run = None
    with q1:
        if st.button("Paridade Ureia vs MAP", width="stretch"):
            prompt_to_run = "Analise o comportamento recente de preços e a paridade de mercado entre Ureia e MAP com base no histórico do FertiPartner."
    with q2:
        if st.button("Riscos Portuários e Frete", width="stretch"):
            prompt_to_run = "Com base nas notícias dos últimos 7 dias, quais são os principais gargalos e riscos de frete nos portos brasileiros de fertilizantes?"
    with q3:
        if st.button("Dependência de KCl no Brasil", width="stretch"):
            prompt_to_run = "Qual é o balanço de abastecimento de Cloreto de Potássio (KCl) no Brasil, quem são os principais países fornecedores e qual a taxa de dependência externa?"
    with q4:
        if st.button("Resumo do Sentimento 7d", width="stretch"):
            prompt_to_run = "Apresente um resumo consolidado dos 5 barômetros de sentimento de mercado de fertilizantes calculados nos últimos 7 dias."

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Exibição do histórico de mensagens
    chat_container = st.container()
    with chat_container:
        if not st.session_state.ai_chat_history:
            st.markdown(
                """
                <div style="
                    background: #FFFFFF;
                    border: 1px dashed #CBD5E1;
                    border-radius: 12px;
                    padding: 2rem;
                    text-align: center;
                    color: #64748B;
                    margin: 1rem 0;
                ">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #1B4332; margin-bottom: 0.5rem;">
                        Bem-vindo ao FertiPartner.AI
                    </div>
                    <div style="font-size: 0.88rem; line-height: 1.5; max-width: 600px; margin: 0 auto;">
                        Faça perguntas sobre cotações, rotas de importação, balanço de consumo de safras, relação de troca e dados agronômicos. O FertiPartner.AI consultará automaticamente as bases de dados e fatos recentes para formular análises precisas.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.ai_chat_history:
                if msg.role == ChatRole.USER:
                    with st.chat_message("user"):
                        st.markdown(msg.content)
                elif msg.role == ChatRole.MODEL and msg.content:
                    with st.chat_message("assistant"):
                        st.markdown(msg.content)

    # Input do Chat
    user_input = st.chat_input("Digite sua dúvida estratégica, econômica ou agronômica sobre fertilizantes...")
    if prompt_to_run:
        user_input = prompt_to_run

    if user_input:
        # Exibe mensagem do usuário imediatamente
        with st.chat_message("user"):
            st.markdown(user_input)

        orchestrator = FertiAIService.get_orchestrator()

        with st.chat_message("assistant"):
            with st.spinner("FertiPartner.AI consultando bases de dados e formulando análise..."):
                response, updated_history = orchestrator.ask(
                    history=st.session_state.ai_chat_history,
                    user_prompt=user_input,
                )

                if response.is_success:
                    st.markdown(response.content)
                    if response.tools_used:
                        tools_label = ", ".join([t.replace("get_", "").replace("_", " ").title() for t in response.tools_used])
                        st.caption(f"Fontes e ferramentas consultadas: {tools_label}")
                    st.session_state.ai_chat_history = updated_history
                else:
                    st.error(response.error_message or "Ocorreu um erro ao processar sua consulta.")

    st.divider()
    render_source_badge("FertiPartner.AI • Google Gemini API • PostgREST 4NF • Feed RSS 7 Dias", "RAG Híbrido & Tools")


if __name__ == "__main__":
    render_view()

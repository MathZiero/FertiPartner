"""View principal da página dedicada do FertiPartner.AI."""

import streamlit as st

from app.domain.ai.entities import ChatMessage, ChatRole
from app.presentation.streamlit.components.ui import render_header
from app.presentation.streamlit.services.ai_service import FertiAIService


def render_view() -> None:
    """Renderiza a interface de chat analítico do FertiPartner.AI."""
    render_header(
        title="FertiPartner.AI - Inteligência Analítica de Mercado",
        subtitle="Assistente analítico especialista em fertilizantes, cotações de mercado, rotas comerciais, balanço de abastecimento e fatos recentes do setor.",
        badge_text="Powered by Google Gemini",
        badge_type="emerald",
    )

    api_key = FertiAIService.get_api_key()

    # Se não houver chave configurada, bloqueia os recursos de IA e exibe a tela de configuração
    if not api_key:
        FertiAIService.render_api_key_setup_card()
        return

    # Inicializa histórico na sessão
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Barra superior de controle de modelo e sessão
    c_model, c_clear, c_disconnect = st.columns([5, 1.5, 1.5])
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

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

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
                        st.caption(f"Fontes consultadas: {tools_label}")
                    st.session_state.ai_chat_history = updated_history
                else:
                    st.error(response.error_message or "Ocorreu um erro ao processar sua consulta.")


if __name__ == "__main__":
    render_view()

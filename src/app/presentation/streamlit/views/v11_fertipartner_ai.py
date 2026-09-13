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

    # Se não houver chave configurada (nem no .env/st.secrets nem informada pelo usuário)
    if not api_key:
        FertiAIService.render_api_key_setup_card()
        return

    # Inicializa histórico na sessão
    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Barra de status da credencial e controle de modelo
    is_user_key = FertiAIService.is_using_user_key()
    active_masked = FertiAIService.get_masked_active_key()

    c_model, c_clear, c_opt = st.columns([5, 1.5, 2.0])
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
            help="Se o modelo selecionado atingir o limite de quota ou sobrecarga temporária, o sistema fará failover automático para os demais modelos da lista.",
        )
        if sel_model != curr_model:
            FertiAIService.set_selected_model(sel_model)
            st.rerun()

    with c_clear:
        if st.button("Limpar Chat", width="stretch"):
            st.session_state.ai_chat_history = []
            st.rerun()

    with c_opt:
        if is_user_key:
            if st.button("Restaurar Padrão", width="stretch", help="Reverte para a chave padrão gratuita do sistema"):
                FertiAIService.clear_user_key()
                st.rerun()
        else:
            st.markdown(
                f"<div style='font-size: 0.78rem; color: #2D6A4F; font-weight: 600; text-align: center; padding-top: 0.5rem;'>"
                f"🟢 Chave Padrão Ativa ({active_masked})"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Expander discreto para chave própria opcional (BYOK)
    with st.expander("🔑 Configurar Chave Própria do Google Gemini (Opcional)", expanded=False):
        st.caption(
            "O FertiPartner.AI já está ativo com a chave padrão do sistema gratuita e resiliência de quotas. "
            "Caso você possua uma chave própria do Google AI Studio e prefira utilizá-la, configure abaixo:"
        )
        col_k, col_b = st.columns([4, 1.5])
        with col_k:
            custom_key_in = st.text_input(
                "Sua chave pessoal Gemini:",
                type="password",
                placeholder="AIzaSy...",
                key="input_user_custom_key",
                label_visibility="collapsed",
            )
        with col_b:
            if st.button("Aplicar Minha Chave", width="stretch", type="primary"):
                if custom_key_in and len(custom_key_in.strip()) > 15:
                    FertiAIService.set_user_key(custom_key_in)
                    st.success("Chave personalizada ativada com sucesso!")
                    st.rerun()
                else:
                    st.error("Insira uma chave válida.")

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
                    meta_info = []
                    if response.tools_used:
                        tools_label = ", ".join([t.replace("get_", "").replace("_", " ").title() for t in response.tools_used])
                        meta_info.append(f"Fontes consultadas: {tools_label}")
                    if response.model_used:
                        meta_info.append(f"Modelo: {response.model_used}")
                    if meta_info:
                        st.caption(" • ".join(meta_info))
                    st.session_state.ai_chat_history = updated_history
                else:
                    st.error(response.error_message or "Ocorreu um erro ao processar sua consulta.")


if __name__ == "__main__":
    render_view()

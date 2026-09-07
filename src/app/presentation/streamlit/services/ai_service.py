"""Serviço de apresentação para integração do FertiPartner.AI no Streamlit."""

import os
import streamlit as st

from app.infrastructure.ai.gemini_client import GeminiClient
from app.application.use_cases.ai.copilot_orchestrator import FertiPartnerAIOrchestrator
from app.application.use_cases.ai.product_diagnostic_use_case import ProductDiagnosticUseCase
from app.application.use_cases.ai.executive_briefing_use_case import ExecutiveBriefingUseCase


class FertiAIService:
    """Gerencia a sessão e clientes de IA na camada de apresentação Streamlit."""

    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]

    @classmethod
    def get_api_key(cls) -> str:
        """Obtém a chave da API do Gemini da sessão ou do ambiente."""
        return (
            st.session_state.get("gemini_api_key", "").strip()
            or os.environ.get("GEMINI_API_KEY", "").strip()
        )

    @classmethod
    def set_api_key(cls, api_key: str) -> None:
        """Armazena a chave na sessão e no ambiente da execução."""
        clean_key = api_key.strip()
        st.session_state["gemini_api_key"] = clean_key
        if clean_key:
            os.environ["GEMINI_API_KEY"] = clean_key

    @classmethod
    def clear_api_key(cls) -> None:
        """Remove a chave da sessão e do ambiente."""
        st.session_state.pop("gemini_api_key", None)
        os.environ.pop("GEMINI_API_KEY", None)

    @classmethod
    def get_selected_model(cls) -> str:
        """Obtém o modelo selecionado."""
        return st.session_state.get("gemini_model", "gemini-2.5-flash")

    @classmethod
    def set_selected_model(cls, model_name: str) -> None:
        """Atualiza o modelo selecionado."""
        st.session_state["gemini_model"] = model_name

    @classmethod
    def get_client(cls) -> GeminiClient:
        """Retorna o cliente Gemini configurado."""
        return GeminiClient(
            api_key=cls.get_api_key(),
            model_name=cls.get_selected_model(),
        )

    @classmethod
    def get_orchestrator(cls) -> FertiPartnerAIOrchestrator:
        """Retorna o orquestrador conversacional."""
        return FertiPartnerAIOrchestrator(cls.get_client())

    @classmethod
    def get_product_diagnostic_use_case(cls) -> ProductDiagnosticUseCase:
        """Retorna o caso de uso de diagnóstico de produto."""
        return ProductDiagnosticUseCase(cls.get_client())

    @classmethod
    def get_executive_briefing_use_case(cls) -> ExecutiveBriefingUseCase:
        """Retorna o caso de uso de briefing executivo."""
        return ExecutiveBriefingUseCase(cls.get_client())

    @classmethod
    def render_api_key_setup_card(cls) -> None:
        """Renderiza o formulário de configuração da chave de API do Google Gemini."""
        st.info(
            """
            **FertiPartner.AI Requer uma Chave de API do Google Gemini**
            
            Para utilizar a inteligência analítica em tempo real, diagnósticos automáticos e consultas via linguagem natural, configure sua chave do Google Gemini.
            """
        )

        with st.container(border=True):
            st.markdown(
                """
                <div style="font-size: 0.95rem; font-weight: 700; color: #1B4332; margin-bottom: 0.5rem;">
                    Como Obter Sua Chave Gratuita em 1 Minuto:
                </div>
                <ol style="font-size: 0.85rem; color: #374151; line-height: 1.6; margin-bottom: 1rem;">
                    <li>Acesse o <b>Google AI Studio</b> através do link oficial: <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #2D6A4F; font-weight: 600;">aistudio.google.com/app/apikey</a></li>
                    <li>Faça login com sua conta Google comum.</li>
                    <li>Clique em <b>"Create API key"</b> e copie o código gerado.</li>
                    <li>Cole a chave no campo abaixo e clique em <b>"Ativar FertiPartner.AI"</b>.</li>
                </ol>
                """,
                unsafe_allow_html=True,
            )

            c_key, c_btn = st.columns([4, 1.5])
            with c_key:
                new_key = st.text_input(
                    "Chave de API do Google Gemini (GEMINI_API_KEY):",
                    type="password",
                    placeholder="AIzaSy...",
                    key="input_setup_gemini_key",
                )
            with c_btn:
                st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                if st.button("Ativar FertiPartner.AI", width="stretch", type="primary"):
                    if new_key and len(new_key.strip()) > 15:
                        cls.set_api_key(new_key)
                        st.success("Chave configurada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Insira uma chave válida do Google Gemini.")

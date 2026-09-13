"""Serviço de apresentação para integração do FertiPartner.AI no Streamlit com suporte a chaves padrão e BYOK."""

import os
import streamlit as st

from app.infrastructure.ai.gemini_client import GeminiClient, mask_secret
from app.application.use_cases.ai.copilot_orchestrator import FertiPartnerAIOrchestrator
from app.application.use_cases.ai.product_diagnostic_use_case import ProductDiagnosticUseCase
from app.application.use_cases.ai.executive_briefing_use_case import ExecutiveBriefingUseCase


class FertiAIService:
    """Gerencia a sessão e clientes de IA na camada de apresentação Streamlit."""

    AVAILABLE_MODELS = list(GeminiClient.DEFAULT_FALLBACK_MODELS)

    @classmethod
    def get_system_default_key(cls) -> str:
        """Obtém a chave padrão do sistema via .env (desenvolvimento local) ou st.secrets (produção)."""
        return GeminiClient._resolve_env_key()

    @classmethod
    def get_user_key(cls) -> str:
        """Obtém a chave customizada fornecida pelo usuário na sessão atual, se houver."""
        try:
            return (
                st.session_state.get("user_gemini_api_key", "").strip()
                or st.session_state.get("gemini_api_key", "").strip()
            )
        except Exception:
            return ""

    @classmethod
    def is_using_user_key(cls) -> bool:
        """Indica se a chave ativa veio de personalização do usuário via UI."""
        user_key = cls.get_user_key()
        return bool(user_key and len(user_key) > 10)

    @classmethod
    def has_default_key(cls) -> bool:
        """Indica se há uma chave padrão do sistema configurada (.env ou st.secrets)."""
        return bool(cls.get_system_default_key())

    @classmethod
    def get_api_key(cls) -> str:
        """Obtém a chave ativa respeitando a precedência: Usuário (se informada) > Sistema (.env/st.secrets)."""
        user_key = cls.get_user_key()
        if user_key and len(user_key) > 10:
            return user_key
        return cls.get_system_default_key()

    @classmethod
    def set_user_key(cls, api_key: str) -> None:
        """Armazena a chave customizada fornecida pelo usuário na sessão."""
        clean = api_key.strip().strip("\"'")
        try:
            st.session_state["user_gemini_api_key"] = clean
            st.session_state["gemini_api_key"] = clean
        except Exception:
            pass

    @classmethod
    def clear_user_key(cls) -> None:
        """Remove a chave customizada do usuário, revertendo imediatamente para o padrão do sistema."""
        try:
            st.session_state.pop("user_gemini_api_key", None)
            st.session_state.pop("gemini_api_key", None)
        except Exception:
            pass

    # Aliases de retrocompatibilidade
    set_api_key = set_user_key
    clear_api_key = clear_user_key

    @classmethod
    def get_masked_active_key(cls) -> str:
        """Retorna representação mascarada segura da chave ativa para logs e UI."""
        return mask_secret(cls.get_api_key())

    @classmethod
    def get_selected_model(cls) -> str:
        """Obtém o modelo selecionado."""
        try:
            return st.session_state.get("gemini_model", GeminiClient.DEFAULT_MODEL)
        except Exception:
            return GeminiClient.DEFAULT_MODEL

    @classmethod
    def set_selected_model(cls, model_name: str) -> None:
        """Atualiza o modelo selecionado."""
        try:
            st.session_state["gemini_model"] = model_name
        except Exception:
            pass

    @classmethod
    def get_available_models(cls) -> list[str]:
        """Retorna a lista exata de modelos configurados e suportados para o FertiPartner.AI."""
        return list(cls.AVAILABLE_MODELS)

    @classmethod
    def get_client(cls) -> GeminiClient:
        """Retorna o cliente Gemini configurado com a chave ativa e pool de resiliência."""
        return GeminiClient(
            api_key=cls.get_api_key(),
            model_name=cls.get_selected_model(),
            fallback_models=cls.AVAILABLE_MODELS,
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
        """Renderiza o formulário de configuração quando nenhuma chave padrão está disponível."""
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
                    <li><b>Para desenvolvimento local:</b> adicione <code>GEMINI_API=sua_chave</code> no arquivo <code>.env</code>.</li>
                    <li><b>Para produção:</b> adicione em <b>Settings > Secrets</b> no painel do Streamlit Cloud.</li>
                    <li>Ou cole a chave no campo abaixo para utilização nesta sessão:</li>
                </ol>
                """,
                unsafe_allow_html=True,
            )

            c_key, c_btn = st.columns([4, 1.5])
            with c_key:
                new_key = st.text_input(
                    "Chave de API do Google Gemini (GEMINI_API):",
                    type="password",
                    placeholder="AIzaSy...",
                    key="input_setup_gemini_key",
                )
            with c_btn:
                st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                if st.button("Ativar FertiPartner.AI", width="stretch", type="primary"):
                    if new_key and len(new_key.strip()) > 15:
                        cls.set_user_key(new_key)
                        st.success("Chave configurada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Insira uma chave válida do Google Gemini.")

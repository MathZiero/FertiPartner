"""Testes ponta a ponta (E2E) para a interface do Copiloto FertiPartner.AI."""

import pytest
from selenium.webdriver.common.by import By
from tests.e2e.pages.dashboard_page import DashboardPage


class TestE2EAICopilot:
    """Validações da interface de conversação inteligente do assistente FertiPartner.AI."""

    def test_ai_copilot_page_renders_cleanly(self, driver, app_url):
        """Valida que a página do copiloto IA é renderizada sem exceções no DOM."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("fertipartner-ai")

        page.assert_no_streamlit_exceptions()

        headers = page.get_headers()
        header_text = " ".join(headers).lower()
        assert "fertipartner.ai" in header_text or "assistente" in header_text or "ia" in header_text

    def test_ai_copilot_chat_interface_components_present(self, driver, app_url):
        """Valida a presença dos elementos de interação de chat (chat input ou mensagens)."""
        page = DashboardPage(driver=driver, base_url=app_url)
        page.open_url("fertipartner-ai")

        page.assert_no_streamlit_exceptions()

        # Verifica se o componente de entrada de chat ou botões de sugestão rápida existem no DOM
        chat_inputs = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stChatInput'], .stChatInput, button")
        assert len(chat_inputs) >= 1, "A interface do FertiPartner.AI deve conter controles interativos de chat"

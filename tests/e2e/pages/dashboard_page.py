"""Page Object para a navegação e componentes do Dashboard FertiPartner."""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Encapsula operações específicas do dashboard multipáginas do FertiPartner."""

    # 100% das rotas da aplicação
    ROUTES_VISAO_GERAL = [
        "",                     # Início (Home)
        "inicio",               # Início explicit
        "readme",               # Documentação Oficial (README)
    ]

    ROUTES_CATALOGO_NPK = [
        # Nitrogenados
        "fert-ureia",
        "fert-amonia-anidra",
        "fert-nitrato-de-amonio",
        "fert-sulfato-de-amonio",
        # Fosfatados
        "fert-map",
        "fert-dap",
        "fert-ssp",
        "fert-tsp",
        "fert-rocha-fosfatica",
        # Potássicos
        "fert-cloreto-de-potassio",
        "fert-sulfato-de-potassio",
        # Secundários
        "fert-enxofre-elementar",
        # Micronutrientes
        "fert-micronutrientes",
    ]

    ROUTES_INTELIGENCIA_INFRA = [
        "analises-comparativas",
        "noticias-mercado",
        "fertipartner-ai",
        "observabilidade",
        "software",
    ]

    ALL_ROUTES = ROUTES_VISAO_GERAL + ROUTES_CATALOGO_NPK + ROUTES_INTELIGENCIA_INFRA

    def get_sidebar_links(self) -> list[str]:
        """Retorna os textos de todos os links de navegação visíveis na barra lateral."""
        links = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSidebar'] a, [data-testid='stSidebarNav'] a")
        return [l.text.strip() for l in links if l.text.strip()]

    def select_dropdown_option_by_label(self, select_box_index: int, target_option: str) -> None:
        """Abre um st.selectbox pelo índice e seleciona a opção desejada."""
        selects = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
        if select_box_index < len(selects):
            box = selects[select_box_index]
            box.click()
            # Aguarda a abertura do menu de opções no DOM
            time.sleep(0.5)
            options = self.driver.find_elements(By.CSS_SELECTOR, "li[role='option'], div[data-baseweb='menu'] li")
            for opt in options:
                if target_option.lower() in opt.text.lower():
                    opt.click()
                    self.wait_for_streamlit_ready()
                    return

    def send_chat_message(self, message: str) -> None:
        """Digita e envia uma mensagem na interface de chat do FertiPartner.AI."""
        chat_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stChatInput'] textarea, .stChatInput textarea"))
        )
        chat_input.send_keys(message)
        # Pressiona enter ou clica no botão de envio
        from selenium.webdriver.common.keys import Keys
        chat_input.send_keys(Keys.ENTER)
        self.wait_for_streamlit_ready()

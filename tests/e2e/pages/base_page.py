"""Base Page Object para automação Selenium com componentes Streamlit."""

import time
from typing import Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    """Encapsula seletores e esperas explícitas para a interface do Streamlit."""

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:8501") -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def open_url(self, path: str = "") -> "BasePage":
        """Abre uma rota específica no Streamlit e aguarda a renderização."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        self.driver.get(url)
        self.wait_for_streamlit_ready()
        return self

    def wait_for_streamlit_ready(self, timeout: int = 20) -> None:
        """Aguarda a hidratação completa da aplicação e o encerramento de spinners de carga."""
        # 1. Espera container raiz do Streamlit
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stAppViewContainer']"))
        )

        # 2. Aguarda estabilização de requisições e animações
        time.sleep(1.5)

        # 3. Aguarda que spinners de carregamento finalizem
        try:
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".stSpinner, [data-testid='stStatusWidget']"))
            )
        except Exception:
            pass

    def assert_no_streamlit_exceptions(self) -> None:
        """Garante rigorosamente que nenhuma exceção Python ou erro de renderização ocorreu no DOM."""
        exceptions = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stException'], .stException")
        if exceptions:
            err_texts = [e.text.strip() for e in exceptions if e.text.strip()]
            raise AssertionError(f"Exceção encontrada na página {self.driver.current_url}:\n" + "\n---\n".join(err_texts))

        # Checa alertas de erro críticos (ex: st.error)
        alerts = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stAlert'][data-test-color='red'], .element-container .stAlert")
        for alert in alerts:
            text = alert.text.lower()
            if "traceback" in text or "error:" in text or "failed to load" in text:
                raise AssertionError(f"Alerta de erro crítico detectado na página {self.driver.current_url}: {alert.text}")

    def get_headers(self) -> list[str]:
        """Retorna todos os títulos (H1, H2, H3) visíveis na página."""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, [data-testid='stHeader']")
        return [h.text.strip() for h in headers if h.text.strip()]

    def count_plotly_charts(self) -> int:
        """Retorna o número de gráficos Plotly interativos renderizados no DOM."""
        charts = self.driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot, [data-testid='stPlotlyChart']")
        return len(charts)

    def count_metrics(self) -> int:
        """Retorna o número de cartões de métricas (st.metric) na página."""
        metrics = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stMetric']")
        return len(metrics)

    def count_dataframes(self) -> int:
        """Retorna o número de DataFrames ou tabelas Streamlit."""
        dfs = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stDataFrame'], [data-testid='stTable']")
        return len(dfs)

    def count_download_buttons(self) -> int:
        """Retorna o número de botões de download CSV disponíveis."""
        btns = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='stDownloadButton'], .stDownloadButton button")
        return len(btns)

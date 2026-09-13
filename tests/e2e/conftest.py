"""Fixtures do pytest para testes ponta a ponta (E2E) com Selenium WebDriver."""

import os
import time
import pytest
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService


@pytest.fixture(scope="session")
def app_url() -> str:
    """URL base do dashboard Streamlit."""
    return os.environ.get("STREAMLIT_URL", "http://localhost:8501")


@pytest.fixture(scope="session", autouse=True)
def ensure_streamlit_server_is_online(app_url):
    """Verifica se o servidor Streamlit está ativo antes de iniciar a bateria E2E."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(app_url)
                if resp.status_code in (200, 304):
                    return
        except Exception:
            time.sleep(1)
    pytest.skip(f"Servidor Streamlit não está respondendo em {app_url}. Inicie com 'uv run streamlit run main.py'.")


@pytest.fixture(scope="session")
def chrome_options() -> ChromeOptions:
    """Configurações otimizadas do Chrome Headless para Streamlit."""
    opts = ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--log-level=3")
    # Desativa detecção de automação
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    return opts


@pytest.fixture(scope="function")
def driver(chrome_options):
    """Instancia um novo WebDriver Chrome isolado para cada teste."""
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(2)
    try:
        yield driver
    finally:
        try:
            driver.quit()
        except Exception:
            pass

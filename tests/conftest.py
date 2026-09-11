"""Fixtures globais do pytest compartilhadas entre os testes."""

import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """Garante que credenciais dummy de teste existam em ambientes sem .env (ex: CI/CD do GitHub Actions)."""
    env_defaults = {
        "SUPABASE_URL": "https://test-project.supabase.co",
        "SUPABASE_KEY": "test-anon-key-12345",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key-67890",
        "SUPABASE_SCHEMA": "public",
        "SUPABASE_TIMEOUT": "10.0",
        "FRED_API_KEY": "test_fred_key_dummy",
    }
    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value


@pytest.fixture
def sample_fertilizer_payload():
    """Fixture providing a standard raw fertilizer sample."""
    return {
        "name": "Urea",
        "category": "Nitrogenados",
        "nitrogen_percentage": 46.0,
        "phosphorus_percentage": 0.0,
        "potassium_percentage": 0.0,
    }


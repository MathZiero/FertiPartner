"""Testes de integração simulada (mock) para o fluxo completo de repositórios do Supabase."""

from unittest.mock import MagicMock, patch
import pytest

from app.infrastructure.supabase import (
    SupabaseBaseRepository,
    SupabaseClientManager,
    SupabaseConfig,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)


@pytest.fixture(autouse=True)
def reset_manager():
    SupabaseClientManager.reset()
    yield
    SupabaseClientManager.reset()


def test_supabase_full_flow_with_mocked_backend():
    """Verify full end-to-end flow: config -> client -> repository CRUD."""
    config = SupabaseConfig(
        url="https://fake-project.supabase.co",
        key="fake-anon-key",
        service_role_key="fake-service-key",
    )

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Mock insert
    mock_table.insert.return_value.execute.return_value.data = [
        {"id": 42, "name": "Potassium Chloride", "category": "Potassicos"}
    ]

    # Mock select
    mock_query = MagicMock()
    mock_table.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value.data = [
        {"id": 42, "name": "Potassium Chloride", "category": "Potassicos"}
    ]

    with patch(
        "app.infrastructure.supabase.client.create_client",
        return_value=mock_client,
    ):
        client = SupabaseClientManager.get_client(config)
        repo = SupabaseFertilizerRepository(client=client)

        # 1. Insert
        created = repo.insert({"name": "Potassium Chloride", "category": "Potassicos"})
        assert created["id"] == 42
        assert created["name"] == "Potassium Chloride"

        # 2. Retrieve
        retrieved = repo.find_by_id(42)
        assert retrieved is not None
        assert retrieved["name"] == "Potassium Chloride"

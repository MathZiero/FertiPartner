"""Testes unitários rigorosos e de alta exigência dos repositórios Supabase."""

from unittest.mock import MagicMock
import pytest

from app.infrastructure.supabase.exceptions import (
    SupabaseQueryError,
    SupabaseRecordNotFoundError,
)
from app.infrastructure.supabase.repository import (
    SupabaseBaseRepository,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = MagicMock()
    return client


class TestSupabaseBaseRepositoryStrict:
    """Validações de alta rigidez para operações de CRUD no repositório base."""

    def test_insert_success(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value.data = [
            {"id": 1, "name": "Urea", "category": "Nitrogen"}
        ]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        result = repo.insert({"name": "Urea", "category": "Nitrogen"})

        assert result == {"id": 1, "name": "Urea", "category": "Nitrogen"}
        mock_supabase_client.table.assert_called_with("fertilizers")
        mock_table.insert.assert_called_with({"name": "Urea", "category": "Nitrogen"})

    def test_insert_raises_query_error_on_db_exception(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.side_effect = Exception("PostgREST timeout")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.insert({"name": "Urea"})

    def test_insert_many_empty_list_returns_immediately(self, mock_supabase_client):
        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        res = repo.insert_many([])
        assert res == []
        mock_supabase_client.table.assert_not_called()

    def test_insert_many_success(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        items_to_insert = [
            {"name": "Urea", "category": "Nitrogen"},
            {"name": "DAP", "category": "Phosphorus"},
        ]
        mock_table.insert.return_value.execute.return_value.data = [
            {"id": 1, "name": "Urea", "category": "Nitrogen"},
            {"id": 2, "name": "DAP", "category": "Phosphorus"},
        ]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        results = repo.insert_many(items_to_insert)

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

    def test_insert_many_raises_query_error_on_failure(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.side_effect = Exception("Connection closed")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.insert_many([{"id": 1}])

    def test_find_by_id_found(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1, "name": "Urea"}]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        result = repo.find_by_id(1)

        assert result == {"id": 1, "name": "Urea"}
        mock_table.select.assert_called_with("*")
        mock_query.eq.assert_called_with("id", 1)

    def test_find_by_id_not_found(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value.data = []

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        result = repo.find_by_id(999)

        assert result is None

    def test_find_by_id_raises_query_error_on_failure(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.side_effect = Exception("DB Connection Lost")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.find_by_id(1)

    def test_find_all_with_pagination_and_order(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1}, {"id": 2}]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        results = repo.find_all(limit=10, offset=20, order_by="name", ascending=True)

        assert len(results) == 2
        mock_query.range.assert_called_with(20, 29)
        mock_query.order.assert_called_with("name", desc=False)

    def test_find_where_filters(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1, "category": "Nitrogen"}]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        results = repo.find_where({"category": "Nitrogen"}, limit=50)

        assert len(results) == 1
        mock_query.eq.assert_called_with("category", "Nitrogen")
        mock_query.limit.assert_called_with(50)

    def test_find_where_raises_query_error_on_failure(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.select.side_effect = Exception("Network down")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.find_where({"name": "Urea"})

    def test_update_success(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1, "name": "Updated Urea"}]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        result = repo.update(1, {"name": "Updated Urea"})

        assert result == {"id": 1, "name": "Updated Urea"}
        mock_table.update.assert_called_with({"name": "Updated Urea"})
        mock_query.eq.assert_called_with("id", 1)

    def test_update_not_found_raises_record_not_found(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value.data = []

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseRecordNotFoundError, match="Record with id 999 not found"):
            repo.update(999, {"name": "Test"})

    def test_update_raises_query_error_on_db_exception(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.update.side_effect = Exception("DB Disk Full")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.update(1, {"name": "Fail"})

    def test_delete_success(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1}]

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        deleted = repo.delete(1)

        assert deleted is True
        mock_table.delete.assert_called_once()
        mock_query.eq.assert_called_with("id", 1)

    def test_delete_not_found_returns_false(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value.data = []

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        deleted = repo.delete(999)

        assert deleted is False

    def test_delete_raises_query_error_on_db_exception(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.delete.side_effect = Exception("Foreign key constraint")

        repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
        with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
            repo.delete(1)


class TestSpecializedRepositoriesStrict:
    """Validações de alta rigidez para os repositórios especializados."""

    def test_raw_data_repository_save_and_find_by_source(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value.data = [
            {
                "id": "rd-001",
                "source_id": "FAOSTAT",
                "collected_at": "2026-08-30T12:00:00",
                "reference_date": "2026-01-01",
                "raw_payload": {"production": 120000},
                "status": "RAW",
            }
        ]

        repo = SupabaseRawDataRepository(client=mock_supabase_client)
        assert repo.table_name == "raw_data"

        result = repo.save_raw_payload(
            source_id="FAOSTAT",
            collected_at="2026-08-30T12:00:00",
            reference_date="2026-01-01",
            raw_payload={"production": 120000},
            status="RAW",
        )
        assert result["id"] == "rd-001"
        assert result["source_id"] == "FAOSTAT"

        # Test find_by_source helper
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": "rd-001", "source_id": "FAOSTAT"}]

        found = repo.find_by_source("FAOSTAT", limit=10)
        assert len(found) == 1
        assert found[0]["source_id"] == "FAOSTAT"

    def test_fertilizer_repository_find_by_name_and_category(self, mock_supabase_client):
        mock_table = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value.data = [{"id": 1, "name": "Urea", "category": "Nitrogenados"}]

        repo = SupabaseFertilizerRepository(client=mock_supabase_client)
        assert repo.table_name == "fertilizers"

        # 1. find_by_name
        fert = repo.find_by_name("Urea")
        assert fert is not None
        assert fert["name"] == "Urea"

        # 2. find_by_category
        mock_query.execute.return_value.data = [
            {"id": 1, "name": "Urea", "category": "Nitrogenados"},
            {"id": 2, "name": "Ammonia", "category": "Nitrogenados"},
        ]
        category_ferts = repo.find_by_category("Nitrogenados")
        assert len(category_ferts) == 2

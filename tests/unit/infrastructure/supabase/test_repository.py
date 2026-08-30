"""Unit tests for Supabase repositories."""

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


def test_insert_success(mock_supabase_client):
    """Verify insert operation executes table query and returns created item."""
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


def test_insert_many_success(mock_supabase_client):
    """Verify insert_many executes bulk insertion."""
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


def test_find_by_id_found(mock_supabase_client):
    """Verify find_by_id returns entity when found."""
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


def test_find_by_id_not_found(mock_supabase_client):
    """Verify find_by_id returns None when entity does not exist."""
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


def test_find_all_with_pagination_and_order(mock_supabase_client):
    """Verify find_all configures limit, offset, and ordering."""
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


def test_find_where_filters(mock_supabase_client):
    """Verify find_where applies dictionary filters correctly."""
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


def test_update_success(mock_supabase_client):
    """Verify update modifies record and returns updated payload."""
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


def test_update_not_found(mock_supabase_client):
    """Verify update raises SupabaseRecordNotFoundError when row is missing."""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table
    mock_query = MagicMock()
    mock_table.update.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.execute.return_value.data = []

    repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
    with pytest.raises(SupabaseRecordNotFoundError, match="Record with id 999 not found"):
        repo.update(999, {"name": "Test"})


def test_delete_success(mock_supabase_client):
    """Verify delete executes deletion and returns True when record was removed."""
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


def test_query_error_wrapping(mock_supabase_client):
    """Verify underlying client exceptions are caught and wrapped in SupabaseQueryError."""
    mock_table = MagicMock()
    mock_supabase_client.table.return_value = mock_table
    mock_table.select.side_effect = Exception("PostgREST connection dropped")

    repo = SupabaseBaseRepository(client=mock_supabase_client, table_name="fertilizers")
    with pytest.raises(SupabaseQueryError, match="Error executing operation on table fertilizers"):
        repo.find_by_id(1)


def test_raw_data_repository_specialization(mock_supabase_client):
    """Verify SupabaseRawDataRepository targets 'raw_data' table and provides helper methods."""
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


def test_fertilizer_repository_specialization(mock_supabase_client):
    """Verify SupabaseFertilizerRepository targets 'fertilizers' table."""
    repo = SupabaseFertilizerRepository(client=mock_supabase_client)
    assert repo.table_name == "fertilizers"

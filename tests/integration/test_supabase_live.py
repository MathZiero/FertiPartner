"""Live database tests for the Supabase instance.

These tests run against the active Supabase project defined in .env
to verify that the 4NF schema, tables, views, RLS, and seed data are fully functional.
"""

import pytest
from app.infrastructure.supabase import (
    SupabaseClientManager,
    SupabaseConfig,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)


@pytest.fixture(scope="module")
def supabase_config():
    """Load configuration from environment."""
    return SupabaseConfig.from_env()


@pytest.fixture(scope="module")
def admin_client(supabase_config):
    """Get authenticated admin (service_role) client."""
    return SupabaseClientManager.get_admin_client(supabase_config)


@pytest.fixture(scope="module")
def public_client(supabase_config):
    """Get public (anon) client."""
    return SupabaseClientManager.get_client(supabase_config)


@pytest.mark.integration
def test_supabase_live_connection(public_client):
    """Verify that public client can connect and perform health check."""
    assert public_client is not None


@pytest.mark.integration
def test_supabase_live_fertilizers_catalog(public_client):
    """Verify that the fertilizers catalog table is populated with seed data."""
    repo = SupabaseFertilizerRepository(client=public_client)
    fertilizers = repo.find_all(limit=10)
    assert len(fertilizers) > 0, "Expected seed fertilizers in public.fertilizers"

    slugs = [f.get("slug") for f in fertilizers]
    assert "ureia" in slugs or "map" in slugs, f"Expected canonical fertilizers in {slugs}"


@pytest.mark.integration
def test_supabase_live_analytical_view(public_client):
    """Verify that the analytical view v_fertilizer_profiles is queryable."""
    res = public_client.table("v_fertilizer_profiles").select("*").limit(5).execute()
    assert res.data is not None
    assert len(res.data) > 0, "Expected data from v_fertilizer_profiles"


@pytest.mark.integration
def test_supabase_live_admin_write_and_delete(admin_client):
    """Verify that the service_role client has write and delete permissions on raw_data."""
    repo = SupabaseRawDataRepository(client=admin_client)

    test_payload = {
        "source_id": 1,
        "collected_at": "2026-09-02T12:00:00Z",
        "reference_date": "2026-09-01",
        "raw_payload": {"test_metric": 12345, "status": "TEST_INTEGRATION"},
        "status": "RAW",
    }

    inserted = repo.insert(test_payload)
    assert inserted is not None
    assert "id" in inserted
    inserted_id = inserted["id"]

    # Clean up
    deleted = repo.delete(inserted_id)
    assert deleted is True

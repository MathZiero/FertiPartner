"""Testes unitários dos coletores de dados (BaseCollector, FRED, Comex Stat e UN Comtrade)."""

from unittest.mock import MagicMock, patch
import pytest
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.collectors.fred_collector import FREDCollector
from app.infrastructure.collectors.comex_stat_collector import ComexStatCollector, normalize_str


class DummyCollector(BaseCollector):
    def run(self, **kwargs):
        return {"status": "SUCCESS"}


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Mock countries table
    mock_countries_resp = MagicMock()
    mock_countries_resp.data = [
        {"id": 1, "iso2": "BR", "iso3": "BRA", "name": "Brasil", "numeric_code": 76},
        {"id": 4, "iso2": "US", "iso3": "USA", "name": "Estados Unidos", "numeric_code": 840},
    ]
    # Mock fertilizers table
    mock_fert_resp = MagicMock()
    mock_fert_resp.data = [
        {"id": 1, "slug": "ureia"},
        {"id": 2, "slug": "map"},
        {"id": 3, "slug": "dap"},
    ]

    def mock_table(name):
        tbl = MagicMock()
        if name == "countries":
            tbl.select.return_value.execute.return_value = mock_countries_resp
        elif name == "fertilizers":
            tbl.select.return_value.execute.return_value = mock_fert_resp
        elif name == "data_collection_runs":
            insert_mock = MagicMock()
            insert_mock.execute.return_value.data = [{"id": "run-uuid-123"}]
            tbl.insert.return_value = insert_mock
            tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
        elif name == "raw_data":
            insert_mock = MagicMock()
            insert_mock.execute.return_value.data = [{"id": 999}]
            tbl.insert.return_value = insert_mock
        else:
            upsert_mock = MagicMock()
            upsert_mock.execute.return_value.data = [{"id": 101}, {"id": 102}]
            tbl.upsert.return_value = upsert_mock
        return tbl

    mock.table.side_effect = mock_table
    return mock


def test_base_collector_resolves_caches(mock_supabase):
    collector = DummyCollector(supabase_client=mock_supabase)
    assert collector.resolve_country_id("BR") == 1
    assert collector.resolve_country_id("bra") == 1
    assert collector.resolve_country_id("Brasil") == 1
    assert collector.resolve_country_id("US") == 4
    assert collector.resolve_country_id("NONEXISTENT") is None

    assert collector.resolve_fertilizer_id("ureia") == 1
    assert collector.resolve_fertilizer_id("map") == 2
    assert collector.resolve_fertilizer_id("unknown") is None


def test_base_collector_auditing(mock_supabase):
    collector = DummyCollector(supabase_client=mock_supabase)
    run_id = collector.start_collection_run(source_id=1, metadata={"test": True})
    assert run_id == "run-uuid-123"

    raw_id = collector.store_raw_payload("https://api.test/data", {"key": "val"}, collection_run_id=run_id)
    assert raw_id == 999

    collector.finish_collection_run(run_id, records_fetched=10, records_inserted=10)


@patch("httpx.Client.request")
def test_fred_collector_execution(mock_http, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "observations": [
            {"date": "2024-01-01", "value": "150.5"},
            {"date": "2024-02-01", "value": "155.2"},
        ]
    }
    mock_http.return_value = mock_resp

    collector = FREDCollector(api_key="mock_key", supabase_client=mock_supabase)
    result = collector.run(
        series_list=[{"series_id": "TEST_SERIES", "fertilizer_slug": "ureia", "benchmark_id": 1}],
        start_date="2024-01-01",
    )

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 2
    assert result["records_inserted"] > 0


@patch("httpx.Client.request")
def test_comex_stat_collector_aggregation(mock_http, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "list": [
                {"coNcm": "31021010", "year": "2024", "monthNumber": "01", "country": "Estados Unidos", "state": "Parana", "metricFOB": "1000", "metricKG": "2000"},
                {"coNcm": "31021010", "year": "2024", "monthNumber": "01", "country": "Estados Unidos", "state": "Mato Grosso", "metricFOB": "3000", "metricKG": "4000"},
            ]
        }
    }
    mock_http.return_value = mock_resp

    collector = ComexStatCollector(supabase_client=mock_supabase)
    result = collector.run(year=2024, month_start=1, month_end=1, flow="import")

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 2
    # Aggregated to 1 bilateral country-level fact
    assert result["records_inserted"] > 0


def test_normalize_str():
    assert normalize_str("São Paulo") == "sao paulo"
    assert normalize_str("Rússia") == "russia"
    assert normalize_str("Catar") == "catar"

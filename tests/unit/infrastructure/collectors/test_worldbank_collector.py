"""Testes unitários do coletor World Bank Indicators API."""

from unittest.mock import MagicMock, patch
import pytest
from app.infrastructure.collectors.worldbank_collector import (
    WorldBankCollector,
    WB_INDICATORS_SOURCE_ID,
    DEFAULT_WB_INDICATORS,
)


@pytest.fixture
def mock_supabase():
    mock = MagicMock()

    mock_countries_resp = MagicMock()
    mock_countries_resp.data = [
        {"id": 1, "iso2": "BR", "iso3": "BRA", "name": "Brasil"},
        {"id": 4, "iso2": "US", "iso3": "USA", "name": "Estados Unidos"},
        {"id": 5, "iso2": "CN", "iso3": "CHN", "name": "China"},
    ]

    mock_runs_resp = MagicMock()
    mock_runs_resp.data = [{"id": "wb-run-uuid-1"}]

    mock_raw_resp = MagicMock()
    mock_raw_resp.data = [{"id": 888}]

    mock_indicators_resp = MagicMock()
    mock_indicators_resp.data = [{"id": 10}, {"id": 11}]

    def mock_table(name):
        tbl = MagicMock()
        if name == "countries":
            tbl.select.return_value.execute.return_value = mock_countries_resp
        elif name == "data_collection_runs":
            tbl.insert.return_value.execute.return_value = mock_runs_resp
            tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
        elif name == "raw_data":
            tbl.insert.return_value.execute.return_value = mock_raw_resp
        elif name == "country_indicators":
            tbl.upsert.return_value.execute.return_value = mock_indicators_resp
        return tbl

    mock.table.side_effect = mock_table
    return mock


def test_worldbank_collector_initialization(mock_supabase):
    collector = WorldBankCollector(supabase_client=mock_supabase)
    assert collector.source_id == WB_INDICATORS_SOURCE_ID
    assert "AG.CON.FERT.ZS" in DEFAULT_WB_INDICATORS


@patch("httpx.Client.request")
def test_worldbank_collector_run_success(mock_http, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"page": 1, "pages": 1, "per_page": 50, "total": 2},
        [
            {
                "indicator": {"id": "AG.CON.FERT.ZS", "value": "Fertilizer consumption (kg/ha)"},
                "country": {"id": "BR", "value": "Brazil"},
                "countryiso3code": "BRA",
                "date": "2023",
                "value": 344.09,
            },
            {
                "indicator": {"id": "AG.CON.FERT.ZS", "value": "Fertilizer consumption (kg/ha)"},
                "country": {"id": "US", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2023",
                "value": 130.50,
            },
            {
                "indicator": {"id": "AG.CON.FERT.ZS", "value": "Fertilizer consumption (kg/ha)"},
                "country": {"id": "US", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2022",
                "value": None,  # Deve ser ignorado
            },
        ],
    ]
    mock_http.return_value = mock_resp

    collector = WorldBankCollector(supabase_client=mock_supabase)
    result = collector.run(
        indicator_id="AG.CON.FERT.ZS",
        country_codes=["BRA", "USA"],
        start_year=2022,
        end_year=2023,
    )

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 3
    assert result["records_inserted"] == 2
    assert result["run_id"] == "wb-run-uuid-1"


@patch("httpx.Client.request")
def test_worldbank_collector_handles_empty_or_malformed_response(mock_http, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"message": [{"id": "120", "key": "Not found"}]}]
    mock_http.return_value = mock_resp

    collector = WorldBankCollector(supabase_client=mock_supabase)
    result = collector.run(
        indicator_id="INVALID_IND",
        country_codes=["BRA"],
    )

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 0
    assert result["records_inserted"] == 0


@patch("httpx.Client.request")
def test_worldbank_collector_handles_http_error(mock_http, mock_supabase):
    mock_http.side_effect = RuntimeError("World Bank API timeout")

    collector = WorldBankCollector(supabase_client=mock_supabase)
    with pytest.raises(RuntimeError, match="World Bank API timeout"):
        collector.run(indicator_id="AG.CON.FERT.ZS", country_codes=["BRA"])

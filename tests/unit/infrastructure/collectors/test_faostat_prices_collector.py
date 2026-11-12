"""Testes unitários do coletor FAOSTAT Input Prices (domínio PP)."""

from unittest.mock import MagicMock, patch
import pytest
from app.infrastructure.collectors.faostat_prices_collector import (
    FAOSTATInputPricesCollector,
    FAOSTAT_PP_SOURCE_ID,
    FAO_PRICE_ITEM_FERTILIZER_MAP,
)


@pytest.fixture
def mock_supabase():
    mock = MagicMock()

    mock_countries_resp = MagicMock()
    mock_countries_resp.data = [
        {"id": 1, "iso2": "BR", "iso3": "BRA", "name": "Brasil"},
        {"id": 4, "iso2": "US", "iso3": "USA", "name": "Estados Unidos"},
    ]

    mock_fert_resp = MagicMock()
    mock_fert_resp.data = [
        {"id": 1, "slug": "ureia"},
        {"id": 2, "slug": "map"},
        {"id": 3, "slug": "dap"},
        {"id": 4, "slug": "cloreto-de-potassio"},
    ]

    mock_runs_resp = MagicMock()
    mock_runs_resp.data = [{"id": "faostat-pp-run-1"}]

    mock_raw_resp = MagicMock()
    mock_raw_resp.data = [{"id": 777}]

    mock_price_resp = MagicMock()
    mock_price_resp.data = [{"id": 101}, {"id": 102}]

    def mock_table(name):
        tbl = MagicMock()
        if name == "countries":
            tbl.select.return_value.execute.return_value = mock_countries_resp
        elif name == "fertilizers":
            tbl.select.return_value.execute.return_value = mock_fert_resp
        elif name == "data_collection_runs":
            tbl.insert.return_value.execute.return_value = mock_runs_resp
            tbl.update.return_value.eq.return_value.execute.return_value.data = [{}]
        elif name == "raw_data":
            tbl.insert.return_value.execute.return_value = mock_raw_resp
        elif name == "price_records":
            tbl.upsert.return_value.execute.return_value = mock_price_resp
        return tbl

    mock.table.side_effect = mock_table
    return mock


def test_faostat_prices_collector_initialization(mock_supabase):
    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    assert collector.source_id == FAOSTAT_PP_SOURCE_ID
    assert "4001" in FAO_PRICE_ITEM_FERTILIZER_MAP


@patch("app.infrastructure.faostat.auth.FAOSTATAuthManager.get_token", return_value="mock_token")
@patch("httpx.Client.request")
def test_faostat_prices_collector_run_success(mock_http, mock_token, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "Area Code": "21",
                "Area": "Brazil",
                "Item Code": "4001",
                "Item": "Urea",
                "Element": "Producer Price (USD/tonne)",
                "Year": 2022,
                "Value": "550.00",
            },
            {
                "Area Code": "21",
                "Area": "Brazil",
                "Item Code": "4022",
                "Item": "DAP",
                "Element": "Producer Price (USD/tonne)",
                "Year": 2022,
                "Value": "780.50",
            },
        ]
    }
    mock_http.return_value = mock_resp

    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    result = collector.run(
        year=2022,
        area_codes=["21"],
    )

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 2
    assert result["records_inserted"] == 2
    assert result["run_id"] == "faostat-pp-run-1"


@patch("app.infrastructure.faostat.auth.FAOSTATAuthManager.get_token", return_value="mock_token")
@patch("httpx.Client.request")
def test_faostat_prices_collector_filters_fertilizer(mock_http, mock_token, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "Area Code": "21",
                "Item Code": "4001",  # Ureia (id 1)
                "Element": "Producer Price (USD/tonne)",
                "Year": 2022,
                "Value": "550.00",
            },
            {
                "Area Code": "21",
                "Item Code": "4022",  # DAP (id 3)
                "Element": "Producer Price (USD/tonne)",
                "Year": 2022,
                "Value": "780.50",
            },
        ]
    }
    mock_http.return_value = mock_resp

    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    result = collector.run(
        year=2022,
        area_codes=["21"],
        fertilizer_id=1,  # Apenas ureia
    )

    assert result["status"] == "SUCCESS"
    assert result["records_fetched"] == 2
    # Apenas o item da Ureia foi persistido
    assert result["records_inserted"] == 2  # mock_price_resp returns 2 in mock


def test_faostat_prices_resolve_benchmark_id(mock_supabase):
    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    # Brasil + Ureia -> 3 (BRAZIL_UREA_CFR)
    assert collector.resolve_benchmark_id(area_code="21", fertilizer_id=1) == 3
    # Brasil + KCl -> 7 (BRAZIL_POTASH_CFR)
    assert collector.resolve_benchmark_id(area_code="21", fertilizer_id=4) == 7
    # US + Ureia -> 2 (US_GULF_UREA_FOB)
    assert collector.resolve_benchmark_id(area_code="231", fertilizer_id=1) == 2
    # US + DAP -> 4 (US_GULF_DAP_FOB)
    assert collector.resolve_benchmark_id(area_code="231", fertilizer_id=3) == 4


@patch("app.infrastructure.faostat.auth.FAOSTATAuthManager.get_token", return_value="mock_token")
@patch("httpx.Client.request")
def test_faostat_prices_collector_skips_raw_data_when_no_fertilizer_matches(mock_http, mock_token, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"Area Code": "21", "Item Code": "515", "Item": "Apples", "Year": 2022, "Value": "400.0"},
            {"Area Code": "21", "Item Code": "486", "Item": "Bananas", "Year": 2022, "Value": "300.0"},
        ]
    }
    mock_http.return_value = mock_resp

    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    with patch.object(collector, "store_raw_payload") as mock_store_raw:
        result = collector.run(year=2022, area_codes=["21"])
        assert result["status"] == "SUCCESS"
        assert result["records_inserted"] == 0
        mock_store_raw.assert_not_called()


@patch("app.infrastructure.faostat.auth.FAOSTATAuthManager.get_token", return_value="mock_token")
@patch("httpx.Client.request")
def test_faostat_prices_collector_stores_only_matched_fertilizer_items_in_raw_data(mock_http, mock_token, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"Area Code": "21", "Item Code": "515", "Item": "Apples", "Year": 2022, "Value": "400.0"},
            {"Area Code": "21", "Item Code": "4001", "Item": "Urea", "Year": 2022, "Value": "550.0"},
        ],
        "metadata": {"datasource": "FAOSTAT", "processing_time": 0.99},
    }
    mock_http.return_value = mock_resp

    collector = FAOSTATInputPricesCollector(supabase_client=mock_supabase)
    with patch.object(collector, "store_raw_payload", return_value=777) as mock_store_raw:
        collector.run(year=2022, area_codes=["21"])
        mock_store_raw.assert_called_once()
        stored_payload = mock_store_raw.call_args.kwargs["payload_data"]
        assert len(stored_payload["data"]) == 1
        assert stored_payload["data"][0]["Item Code"] == "4001"


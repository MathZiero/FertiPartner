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
    # Mock fertilizer_classifications table
    mock_classif_resp = MagicMock()
    mock_classif_resp.data = [
        {"fertilizer_id": 1, "classification_system": "HS6", "classification_code": "310210"},
        {"fertilizer_id": 2, "classification_system": "HS6", "classification_code": "310540"},
    ]

    def mock_table(name):
        tbl = MagicMock()
        if name == "countries":
            tbl.select.return_value.execute.return_value = mock_countries_resp
            insert_mock = MagicMock()
            insert_mock.execute.return_value.data = [{"id": 99, "numeric_code": 792, "iso2": "TR", "name": "Turquia"}]
            tbl.insert.return_value = insert_mock
        elif name == "fertilizers":
            tbl.select.return_value.execute.return_value = mock_fert_resp
        elif name == "fertilizer_classifications":
            tbl.select.return_value.execute.return_value = mock_classif_resp
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


from app.infrastructure.collectors.comtrade_collector import UNComtradeCollector


def test_un_comtrade_dynamic_classifications_loading(mock_supabase):
    collector = UNComtradeCollector(api_key="mock_key", supabase_client=mock_supabase)
    assert "310210" in collector.hs_fertilizer_map
    assert collector.hs_fertilizer_map["310210"] == 1
    assert "310540" in collector.hs_fertilizer_map
    assert collector.hs_fertilizer_map["310540"] == 2


@patch("httpx.Client.request")
def test_un_comtrade_discover_top_traders(mock_http, mock_supabase):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            # Importers
            {"reporterCode": 76, "flowCode": "M", "partnerCode": 0, "netWgt": 5000000000, "primaryValue": 2000000000},
            {"reporterCode": 840, "flowCode": "M", "partnerCode": 0, "netWgt": 4000000000, "primaryValue": 1500000000},
            {"reporterCode": 792, "flowCode": "M", "partnerCode": 0, "netWgt": 3000000000, "primaryValue": 1000000000},
            # Exporters
            {"reporterCode": 512, "flowCode": "X", "partnerCode": 0, "netWgt": 6000000000, "primaryValue": 2500000000},
            {"reporterCode": 643, "flowCode": "X", "partnerCode": 0, "netWgt": 4500000000, "primaryValue": 1800000000},
        ]
    }
    mock_http.return_value = mock_resp

    collector = UNComtradeCollector(api_key="mock_key", supabase_client=mock_supabase)
    top_traders = collector.discover_top_traders("310210", period=2023, top_n=2)

    assert len(top_traders["importers"]) == 2
    assert top_traders["importers"][0]["reporterCode"] == 76
    assert top_traders["importers"][1]["reporterCode"] == 840

    assert len(top_traders["exporters"]) == 2
    assert top_traders["exporters"][0]["reporterCode"] == 512
    assert top_traders["exporters"][1]["reporterCode"] == 643


@patch("httpx.Client.request")
def test_un_comtrade_ensure_country_exists(mock_http, mock_supabase):
    # Mock partnerAreas reference call
    mock_ref_resp = MagicMock()
    mock_ref_resp.status_code = 200
    mock_ref_resp.json.return_value = {
        "results": [
            {"id": 792, "PartnerCode": 792, "PartnerDesc": "Turkey", "PartnerCodeIsoAlpha2": "TR", "PartnerCodeIsoAlpha3": "TUR", "isGroup": False}
        ]
    }
    mock_http.return_value = mock_ref_resp

    collector = UNComtradeCollector(api_key="mock_key", supabase_client=mock_supabase)
    # 792 not in initial mock_countries (which only has 76 and 840)
    country_id = collector._ensure_country_exists(792)
    assert country_id == 99
    assert collector._countries_by_numeric[792] == 99


@patch("httpx.Client.request")
def test_un_comtrade_run_auto_top_flows(mock_http, mock_supabase):
    mock_world_resp = MagicMock()
    mock_world_resp.status_code = 200
    mock_world_resp.json.return_value = {
        "data": [
            {"reporterCode": 76, "flowCode": "M", "partnerCode": 0, "netWgt": 1000000, "primaryValue": 500000},
            {"reporterCode": 840, "flowCode": "X", "partnerCode": 0, "netWgt": 1000000, "primaryValue": 500000},
        ]
    }

    mock_trade_resp = MagicMock()
    mock_trade_resp.status_code = 200
    mock_trade_resp.json.return_value = {
        "data": [
            {"reporterCode": 76, "partnerCode": 840, "flowCode": "M", "netWgt": 500000, "primaryValue": 250000}
        ]
    }

    def side_effect(*args, **kwargs):
        params = kwargs.get("params", {})
        if params.get("partnerCode") == "0":
            return mock_world_resp
        return mock_trade_resp

    mock_http.side_effect = side_effect

    collector = UNComtradeCollector(api_key="mock_key", supabase_client=mock_supabase)
    result = collector.run_auto_top_flows(period=2023, top_n=2, cmd_codes=["310210"])

    assert result["status"] == "SUCCESS"
    assert result["records_inserted"] > 0


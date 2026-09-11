"""Testes unitários rigorosos (TDD) para validar comportamentos dos scripts CLI de coleta de dados."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

import scripts.collect_benchmark_prices as script_prices
import scripts.collect_brazil_comex as script_comex
import scripts.collect_faostat_production as script_faostat
import scripts.populate_fertilizer_catalog as script_catalog
import scripts.collect_top_trade_flows as script_comtrade
import scripts.collect_worldbank_indicators as script_wb
import scripts.collect_faostat_prices as script_fao_prices

from domain.fertilizers import FERTILIZERS_CATALOG


# ==============================================================================
# 1. TESTES: collect_benchmark_prices.py (FRED)
# ==============================================================================

def test_collect_benchmark_prices_missing_api_key_exits_with_error(monkeypatch, capsys):
    """Comportamento: Se FRED_API_KEY não estiver no ambiente nem for passada via CLI, o script deve falhar com código 1 e mensagem clara."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(script_prices, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr("sys.argv", ["collect_benchmark_prices.py", "--year", "2023"])

    with pytest.raises(SystemExit) as exc_info:
        script_prices.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "FRED_API_KEY" in captured.out
    assert "--api-key" in captured.out


def test_collect_benchmark_prices_dry_run_queries_without_persisting(monkeypatch, capsys):
    """Comportamento: Com --dry-run, consulta observações das séries na API do FRED e exibe sumário sem gravar em price_records."""
    monkeypatch.setenv("FRED_API_KEY", "test_key_123")
    monkeypatch.setattr("sys.argv", ["collect_benchmark_prices.py", "--year", "2023", "--fertilizer", "dap", "--dry-run"])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "observations": [
            {"date": "2023-01-01", "value": "600.0"},
            {"date": "2023-02-01", "value": "620.5"},
        ]
    }

    with patch("app.infrastructure.collectors.fred_collector.ResilientHttpClient.get", return_value=mock_resp), \
         patch("app.infrastructure.supabase.client.get_supabase_admin_client"):
        script_prices.main()

    captured = capsys.readouterr()
    assert "[MODO DRY-RUN]" in captured.out
    assert "Série WPU0652026A" in captured.out
    assert "Observações encontradas: 2" in captured.out
    assert "620.5" in captured.out
    assert "Operação dry-run concluída com sucesso" in captured.out


def test_collect_benchmark_prices_full_run_invokes_collector(monkeypatch, capsys):
    """Comportamento: Execução padrão deve instanciar o FREDCollector e chamar run() com os parâmetros fornecidos."""
    monkeypatch.setenv("FRED_API_KEY", "test_key_123")
    monkeypatch.setattr("sys.argv", ["collect_benchmark_prices.py", "--year", "2024", "--series", "WPU0652013A6"])

    mock_result = {
        "status": "SUCCESS",
        "run_id": "run-uuid-fred-999",
        "records_fetched": 12,
        "records_inserted": 12,
    }

    with patch("scripts.collect_benchmark_prices.FREDCollector") as MockCollectorClass:
        mock_instance = MockCollectorClass.return_value
        mock_instance.run.return_value = mock_result

        script_prices.main()

        mock_instance.run.assert_called_once()
        call_kwargs = mock_instance.run.call_args[1]
        assert call_kwargs["start_date"] == "2024-01-01"
        assert len(call_kwargs["series_list"]) == 1
        assert call_kwargs["series_list"][0]["series_id"] == "WPU0652013A6"

    captured = capsys.readouterr()
    assert "COLETA FRED CONCLUÍDA COM SUCESSO!" in captured.out
    assert "Run ID: run-uuid-fred-999" in captured.out


# ==============================================================================
# 2. TESTES: collect_brazil_comex.py (MDIC Comex Stat)
# ==============================================================================

def test_collect_brazil_comex_dry_run_aggregates_volume_and_fob(monkeypatch, capsys):
    """Comportamento: Com --dry-run, consulta dados na API Comex Stat, calcula volume/FOB total e não persiste no banco."""
    monkeypatch.setattr("sys.argv", [
        "collect_brazil_comex.py",
        "--year", "2024",
        "--flow", "import",
        "--month-start", "1",
        "--month-end", "2",
        "--dry-run",
    ])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "list": [
                {"metricKG": 1000000.0, "metricFOB": 300000.0},
                {"metricKG": 2000000.0, "metricFOB": 700000.0},
            ]
        }
    }

    with patch("app.infrastructure.collectors.comex_stat_collector.ResilientHttpClient.post", return_value=mock_resp), \
         patch("app.infrastructure.supabase.client.get_supabase_admin_client"):
        script_comex.main()

    captured = capsys.readouterr()
    assert "[MODO DRY-RUN / INSPEÇÃO]" in captured.out
    assert "Registros aduaneiros retornados: 2" in captured.out
    assert "Volume total: 3.00 mil MT" in captured.out
    assert "Valor FOB total: $ 1,000,000.00 USD" in captured.out


def test_collect_brazil_comex_full_run_invokes_collector(monkeypatch, capsys):
    """Comportamento: Execução oficial deve chamar o coletor ComexStatCollector para os meses e fluxos configurados."""
    monkeypatch.setattr("sys.argv", [
        "collect_brazil_comex.py",
        "--year", "2024",
        "--flow", "export",
        "--month-start", "1",
        "--month-end", "6",
    ])

    mock_run_res = {"status": "SUCCESS", "records_fetched": 50, "records_inserted": 25}

    with patch("scripts.collect_brazil_comex.ComexStatCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.run.return_value = mock_run_res

        script_comex.main()

        instance.run.assert_called_once_with(
            year=2024,
            month_start=1,
            month_end=6,
            flow="export",
        )

    captured = capsys.readouterr()
    assert "COLETA COMEX STAT CONCLUÍDA COM SUCESSO!" in captured.out
    assert "Fatos de comércio bilateral (4NF) inseridos/atualizados: 25" in captured.out


def test_collect_brazil_comex_invalid_flow_fails(monkeypatch):
    """Comportamento: Valores inválidos para --flow devem ser rejeitados pelo parser CLI com SystemExit."""
    monkeypatch.setattr("sys.argv", ["collect_brazil_comex.py", "--flow", "invalido"])
    with pytest.raises(SystemExit) as exc_info:
        script_comex.main()
    assert exc_info.value.code == 2


# ==============================================================================
# 3. TESTES: collect_faostat_production.py (FAOSTAT / IFA)
# ==============================================================================

def test_collect_faostat_offline_benchmarks_mode(monkeypatch, capsys):
    """Comportamento: Flag --offline-benchmarks deve executar carga direta dos benchmarks consolidados mundiais."""
    monkeypatch.setattr("sys.argv", ["collect_faostat_production.py", "--year", "2024", "--offline-benchmarks"])

    with patch("scripts.collect_faostat_production.run_offline_benchmarks", return_value=32) as mock_bench:
        script_faostat.main()
        mock_bench.assert_called_once_with(target_year=2024)

    captured = capsys.readouterr()
    assert "Total inserido: 32 registros" in captured.out


def test_collect_faostat_dry_run_tests_api_availability(monkeypatch, capsys):
    """Comportamento: Com --dry-run, testa autenticação e consulta de amostra na FAO sem persistir."""
    monkeypatch.setattr("sys.argv", ["collect_faostat_production.py", "--year", "2023", "--dry-run"])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"Item": "Urea", "Value": 1000}]}

    with patch("app.infrastructure.faostat.auth.FAOSTATAuthManager.get_token", return_value="fake_token_jwt"), \
         patch("app.infrastructure.collectors.faostat_collector.ResilientHttpClient.get", return_value=mock_resp), \
         patch("app.infrastructure.supabase.client.get_supabase_admin_client"):
        script_faostat.main()

    captured = capsys.readouterr()
    assert "[MODO DRY-RUN]" in captured.out
    assert "Token FAOSTAT obtido com sucesso" in captured.out
    assert "Resposta recebida da FAOSTAT para área" in captured.out


def test_collect_faostat_fallback_to_benchmarks_on_api_error(monkeypatch, capsys):
    """Comportamento: Se a API online da FAO falhar, deve acionar automaticamente a contingência de benchmarks consolidados."""
    monkeypatch.setattr("sys.argv", ["collect_faostat_production.py", "--year", "2023"])

    with patch("scripts.collect_faostat_production.FAOSTATCollector") as MockCollector, \
         patch("scripts.collect_faostat_production.run_offline_benchmarks", return_value=15) as mock_bench:
        instance = MockCollector.return_value
        instance.run.side_effect = RuntimeError("FAOSTAT server 503 Service Unavailable")

        script_faostat.main()

        mock_bench.assert_called_once_with(target_year=2023)

    captured = capsys.readouterr()
    assert "Aplicando benchmarks mundiais consolidados..." in captured.out


# ==============================================================================
# 4. TESTES: populate_fertilizer_catalog.py (Catálogo de Domínio)
# ==============================================================================

def test_populate_fertilizer_catalog_show(monkeypatch, capsys):
    """Comportamento: --show deve exibir tabela formatada com todos os 7 fertilizantes oficiais e suas garantias nutricionais."""
    monkeypatch.setattr("sys.argv", ["populate_fertilizer_catalog.py", "--show"])

    script_catalog.main()

    captured = capsys.readouterr()
    assert "FERTIPARTNER - CATÁLOGO OFICIAL DE FERTILIZANTES HOMOLOGADOS" in captured.out
    assert "Total de produtos homologados: 12" in captured.out
    for fert in FERTILIZERS_CATALOG:
        assert fert["canonical_name"][:20] in captured.out


def test_populate_fertilizer_catalog_export_json(monkeypatch, tmp_path, capsys):
    """Comportamento: --export-json deve criar arquivo JSON válido contendo a lista integral do catálogo."""
    out_file = tmp_path / "catalogo_exportado.json"
    monkeypatch.setattr("sys.argv", ["populate_fertilizer_catalog.py", "--export-json", str(out_file)])

    script_catalog.main()

    assert out_file.exists()
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == len(FERTILIZERS_CATALOG)
    assert content[0]["canonical_name"] == "Ureia"

    captured = capsys.readouterr()
    assert "Catálogo exportado com sucesso" in captured.out


def test_populate_fertilizer_catalog_sync_db(monkeypatch, capsys):
    """Comportamento: --sync-db deve enviar registros para o Supabase com as colunas esperadas da tabela fertilizers e categories."""
    monkeypatch.setattr("sys.argv", ["populate_fertilizer_catalog.py", "--sync-db", "--year", "2024"])

    mock_client = MagicMock()
    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = MagicMock(data=[{"id": i} for i in range(1, 13)])
    mock_client.table.return_value.upsert.return_value = mock_upsert

    with patch("scripts.populate_fertilizer_catalog.get_supabase_admin_client", return_value=mock_client):
        script_catalog.main()

        # Deve sincronizar fertilizer_categories (incluindo Macronutrientes Secundários e Micronutrientes)
        # e fertilizers (12 produtos)
        calls = [c[0][0] for c in mock_client.table.call_args_list]
        assert "fertilizer_categories" in calls
        assert "fertilizers" in calls

        # A chamada de fertilizers deve ter os 12 itens do catálogo
        fert_upsert_args = None
        for call in mock_client.table.return_value.upsert.call_args_list:
            rows = call[0][0]
            if len(rows) == 12:
                fert_upsert_args = rows
                break

        assert fert_upsert_args is not None, "Esperado upsert de 12 fertilizantes na tabela fertilizers"
        slugs = [r["slug"] for r in fert_upsert_args]
        assert "ssp" in slugs
        assert "tsp" in slugs
        assert "rocha-fosfatica" in slugs
        assert "sulfato-de-potassio" in slugs
        assert "enxofre-elementar" in slugs

    captured = capsys.readouterr()
    assert "fertilizantes sincronizados com o banco de dados" in captured.out


def test_fertilizers_catalog_contains_12_products_with_rich_agronomic_specs():
    """Comportamento: O catálogo mestre deve possuir 12 fertilizantes homologados com fichas técnicas detalhadas."""
    assert len(FERTILIZERS_CATALOG) == 12
    slug_map = {f["slug"]: f for f in FERTILIZERS_CATALOG}

    # Verifica os 5 novos produtos
    for required_slug in ["ssp", "tsp", "rocha-fosfatica", "sulfato-de-potassio", "enxofre-elementar"]:
        assert required_slug in slug_map, f"Fertilizante {required_slug} ausente no catálogo"

    # Verifica campos detalhados em todos os fertilizantes
    for fert in FERTILIZERS_CATALOG:
        assert fert.get("detailed_description"), f"detailed_description ausente em {fert['slug']}"
        assert fert.get("agronomic_usage"), f"agronomic_usage ausente em {fert['slug']}"
        assert fert.get("physical_properties"), f"physical_properties ausente em {fert['slug']}"
        assert fert.get("handling_storage"), f"handling_storage ausente em {fert['slug']}"
        assert fert.get("hs_ncm_codes"), f"hs_ncm_codes ausente em {fert['slug']}"



# ==============================================================================
# 5. TESTES: collect_top_trade_flows.py (UN Comtrade)
# ==============================================================================

def test_collect_top_trade_flows_discover_only(monkeypatch, capsys):
    """Comportamento: --discover-only deve consultar rankings mundiais (partnerCode=0) sem gravar fatos bilaterais no banco."""
    monkeypatch.setattr("sys.argv", [
        "collect_top_trade_flows.py",
        "--year", "2023",
        "--hs", "310210",
        "--top-n", "3",
        "--discover-only",
    ])

    mock_discover = {
        "importers": [{"reporterCode": 76, "qty_mt": 5000000.0, "val_usd": 1500000000.0}],
        "exporters": [{"reporterCode": 643, "qty_mt": 7000000.0, "val_usd": 2100000000.0}],
    }

    with patch("scripts.collect_top_trade_flows.UNComtradeCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.hs_fertilizer_map = {"310210": 1}
        instance.discover_top_traders.return_value = mock_discover

        script_comtrade.main()

        instance.discover_top_traders.assert_called_once_with(
            cmd_code="310210",
            period=2023,
            top_n=3,
        )
        instance.run_auto_top_flows.assert_not_called()

    captured = capsys.readouterr()
    assert "[MODO DESCOBERTA]" in captured.out
    assert "TOP IMPORTADORES:" in captured.out
    assert "TOP EXPORTADORES:" in captured.out


# ==============================================================================
# 6. TESTES: Parâmetro opcional --fertilizer-id nos coletores existentes
# ==============================================================================

def test_collect_brazil_comex_fertilizer_id_filters_ncms(monkeypatch, capsys):
    """Comportamento: --fertilizer-id 1 deve filtrar para consultar apenas NCMs de Ureia (31021010)."""
    monkeypatch.setattr("sys.argv", ["collect_brazil_comex.py", "--year", "2024", "--fertilizer-id", "1", "--dry-run"])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {"list": [{"metricFOB": 1000000.0, "metricKG": 2500000.0}]}
    }

    with patch("app.infrastructure.collectors.comex_stat_collector.ResilientHttpClient.post", return_value=mock_resp):
        script_comex.main()

    captured = capsys.readouterr()
    assert "NCM 31021010 -> Fertilizante ID 1" in captured.out
    assert "NCM 31053000" not in captured.out
    assert "[MODO DRY-RUN / INSPEÇÃO]" in captured.out


def test_collect_faostat_production_fertilizer_id_filter(monkeypatch, capsys):
    """Comportamento: --fertilizer-id 1 com --offline-benchmarks deve filtrar apenas a Ureia (ID 1)."""
    monkeypatch.setattr("sys.argv", ["collect_faostat_production.py", "--year", "2023", "--fertilizer-id", "1", "--offline-benchmarks"])

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"id": 1, "iso2": "CN"}, {"id": 2, "iso2": "BR"}]
    )
    mock_upsert = MagicMock()
    mock_upsert.execute.return_value = MagicMock(data=[{"id": 101}])
    mock_client.table.return_value.upsert.return_value = mock_upsert

    with patch("scripts.collect_faostat_production.get_supabase_admin_client", return_value=mock_client):
        script_faostat.main()

        call_args = mock_client.table.return_value.upsert.call_args
        rows = call_args[0][0]
        # Todos os registros inseridos devem pertencer exclusivamente ao fertilizer_id 1
        assert len(rows) > 0
        assert all(r["fertilizer_id"] == 1 for r in rows)


def test_collect_benchmark_prices_fertilizer_id_filter(monkeypatch, capsys):
    """Comportamento: --fertilizer-id 1 com --dry-run deve selecionar apenas séries FRED da Ureia."""
    monkeypatch.setenv("FRED_API_KEY", "test_key_123")
    monkeypatch.setattr("sys.argv", ["collect_benchmark_prices.py", "--year", "2023", "--fertilizer-id", "1", "--dry-run"])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"observations": [{"date": "2023-01-01", "value": "450.0"}]}

    with patch("app.infrastructure.collectors.fred_collector.ResilientHttpClient.get", return_value=mock_resp):
        script_prices.main()

    captured = capsys.readouterr()
    assert "Série WPU0652013A6" in captured.out or "Série PCU325311325311" in captured.out
    assert "Série WPU0652026A" not in captured.out  # DAP (ID 3) não deve ser chamado


def test_collect_top_trade_flows_fertilizer_id_filter(monkeypatch, capsys):
    """Comportamento: --fertilizer-id 1 deve consultar apenas o código HS 310210 (Ureia)."""
    monkeypatch.setattr("sys.argv", [
        "collect_top_trade_flows.py",
        "--year", "2023",
        "--fertilizer-id", "1",
        "--discover-only",
    ])

    mock_discover = {
        "importers": [{"reporterCode": 76, "qty_mt": 1000.0, "val_usd": 500000.0}],
        "exporters": [{"reporterCode": 643, "qty_mt": 2000.0, "val_usd": 900000.0}],
    }

    with patch("scripts.collect_top_trade_flows.UNComtradeCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.hs_fertilizer_map = {"310210": 1, "310540": 2, "310420": 4}
        instance.discover_top_traders.return_value = mock_discover

        script_comtrade.main()

        instance.discover_top_traders.assert_called_once_with(
            cmd_code="310210",
            period=2023,
            top_n=10,
        )


# ==============================================================================
# 7. TESTES: collect_fertilizer_all_sources.py (Agregador Resiliente)
# ==============================================================================

def test_collect_fertilizer_all_sources_invalid_fertilizer_id(monkeypatch, capsys):
    """Comportamento: Se o fertilizer-id não existir no catálogo, deve falhar com código 1 e exibir IDs válidos."""
    import scripts.collect_fertilizer_all_sources as script_aggregator

    monkeypatch.setattr("sys.argv", ["collect_fertilizer_all_sources.py", "--fertilizer-id", "999", "--year", "2024"])

    with pytest.raises(SystemExit) as exc:
        script_aggregator.main()

    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Fertilizante ID 999 não encontrado" in captured.out
    assert "IDs disponíveis" in captured.out


def test_collect_fertilizer_all_sources_success_all_sources(monkeypatch, capsys):
    """Comportamento: Execução com sucesso em todas as 4 fontes deve imprimir relatório consolidado com status SUCESSO TOTAL."""
    import scripts.collect_fertilizer_all_sources as script_aggregator

    monkeypatch.setattr("sys.argv", [
        "collect_fertilizer_all_sources.py",
        "--fertilizer-id", "1",
        "--year", "2024",
        "--dry-run",
    ])

    with patch.object(script_aggregator, "run_comex_stat_pipeline", return_value={"status": "SUCESSO", "records": 1250, "details": "NCM 31021010"}), \
         patch.object(script_aggregator, "run_faostat_pipeline", return_value={"status": "SUCESSO", "records": 85, "details": "8 polos FAO"}), \
         patch.object(script_aggregator, "run_fred_pipeline", return_value={"status": "SUCESSO", "records": 24, "details": "Série WPU0652013A6"}), \
         patch.object(script_aggregator, "run_comtrade_pipeline", return_value={"status": "SUCESSO", "records": 20, "details": "HS 310210 Top 10"}):

        script_aggregator.main()

    captured = capsys.readouterr()
    assert "FERTIPARTNER - RELATÓRIO CONSOLIDADO DE COLETA INTEGRADA" in captured.out
    assert "Ureia" in captured.out
    assert "Comex Stat (MDIC)" in captured.out
    assert "FAOSTAT" in captured.out
    assert "FRED" in captured.out
    assert "UN Comtrade" in captured.out
    assert "STATUS GERAL: SUCESSO TOTAL (4/4 fontes)" in captured.out


def test_collect_fertilizer_all_sources_fault_tolerant_to_api_failure(monkeypatch, capsys):
    """Comportamento: Falha na API da ONU (ex: 403 Quota Exceeded) não deve derrubar o script; outras fontes continuam e status é PARCIAL."""
    import scripts.collect_fertilizer_all_sources as script_aggregator

    monkeypatch.setattr("sys.argv", [
        "collect_fertilizer_all_sources.py",
        "--fertilizer-id", "1",
        "--year", "2024",
        "--dry-run",
    ])

    with patch.object(script_aggregator, "run_comex_stat_pipeline", return_value={"status": "SUCESSO", "records": 1250, "details": "NCM 31021010"}), \
         patch.object(script_aggregator, "run_faostat_pipeline", return_value={"status": "SUCESSO", "records": 85, "details": "8 polos FAO"}), \
         patch.object(script_aggregator, "run_fred_pipeline", return_value={"status": "SUCESSO", "records": 24, "details": "Série WPU0652013A6"}), \
         patch.object(script_aggregator, "run_comtrade_pipeline", side_effect=Exception("403 Quota Exceeded")):

        script_aggregator.main()

    captured = capsys.readouterr()
    assert "FERTIPARTNER - RELATÓRIO CONSOLIDADO DE COLETA INTEGRADA" in captured.out
    assert "Comex Stat (MDIC)" in captured.out
    assert "UN Comtrade" in captured.out
    assert "FALHA" in captured.out
    assert "403 Quota Exceeded" in captured.out
    assert "STATUS GERAL: SUCESSO PARCIAL (3/4 fontes)" in captured.out


# ==============================================================================
# 8. TESTES: collect_worldbank_indicators.py (World Bank WDI)
# ==============================================================================

def test_collect_worldbank_indicators_dry_run(monkeypatch, capsys):
    """Comportamento: Com --dry-run, consulta amostra na API do Banco Mundial e exibe amostras sem gravar no banco."""
    monkeypatch.setattr("sys.argv", [
        "collect_worldbank_indicators.py",
        "--indicator", "AG.CON.FERT.ZS",
        "--countries", "BRA", "USA",
        "--dry-run",
    ])

    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {"page": 1, "pages": 1, "per_page": 5, "total": 2},
        [
            {"country": {"value": "Brazil"}, "date": "2023", "value": 344.09},
            {"country": {"value": "United States"}, "date": "2023", "value": 130.50},
        ],
    ]

    with patch("scripts.collect_worldbank_indicators.WorldBankCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.http.get.return_value = mock_resp

        script_wb.main()

        instance.run.assert_not_called()
        instance.http.get.assert_called_once()

    captured = capsys.readouterr()
    assert "[MODO DRY-RUN]" in captured.out
    assert "Brazil (2023): 344.09" in captured.out
    assert "United States (2023): 130.5" in captured.out


def test_collect_worldbank_indicators_full_run(monkeypatch, capsys):
    """Comportamento: Execução completa sem --dry-run deve invocar collector.run() com argumentos informados."""
    monkeypatch.setattr("sys.argv", [
        "collect_worldbank_indicators.py",
        "--indicator", "AG.CON.FERT.ZS",
        "--countries", "BRA",
        "--start-year", "2020",
        "--end-year", "2023",
    ])

    with patch("scripts.collect_worldbank_indicators.WorldBankCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.run.return_value = {
            "status": "SUCCESS",
            "run_id": "run-wb-test",
            "records_fetched": 4,
            "records_inserted": 4,
        }

        script_wb.main()

        instance.run.assert_called_once_with(
            indicator_id="AG.CON.FERT.ZS",
            country_codes=["BRA"],
            start_year=2020,
            end_year=2023,
        )

    captured = capsys.readouterr()
    assert "COLETA DO BANCO MUNDIAL CONCLUÍDA COM SUCESSO!" in captured.out
    assert "Total de registros obtidos da API: 4" in captured.out


# ==============================================================================
# 9. TESTES: collect_faostat_prices.py (FAOSTAT PP)
# ==============================================================================

def test_collect_faostat_prices_dry_run(monkeypatch, capsys):
    """Comportamento: Com --dry-run, consulta amostra na API do FAOSTAT PP sem gravar no banco."""
    monkeypatch.setattr("sys.argv", [
        "collect_faostat_prices.py",
        "--year", "2022",
        "--area-codes", "21",
        "--dry-run",
    ])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [
            {"Item": "Urea", "Value": "550.0", "Element": "Producer Price (USD/tonne)"}
        ]
    }

    with patch("scripts.collect_faostat_prices.FAOSTATInputPricesCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.auth_manager.get_token.return_value = "mock_token"
        instance.http.get.return_value = mock_resp

        script_fao_prices.main()

        instance.run.assert_not_called()
        instance.http.get.assert_called_once()

    captured = capsys.readouterr()
    assert "[MODO DRY-RUN]" in captured.out
    assert "Urea: 550.0 USD/MT" in captured.out


def test_collect_faostat_prices_full_run_with_fertilizer_filter(monkeypatch, capsys):
    """Comportamento: Execução com --fertilizer ureia deve mapear slug para ID 1 e invocar collector.run()."""
    monkeypatch.setattr("sys.argv", [
        "collect_faostat_prices.py",
        "--year", "2022",
        "--fertilizer", "ureia",
        "--area-codes", "21",
    ])

    with patch("scripts.collect_faostat_prices.FAOSTATInputPricesCollector") as MockCollector:
        instance = MockCollector.return_value
        instance.run.return_value = {
            "status": "SUCCESS",
            "run_id": "run-fao-pp-test",
            "records_fetched": 1,
            "records_inserted": 1,
        }

        script_fao_prices.main()

        instance.run.assert_called_once_with(
            year=2022,
            area_codes=["21"],
            fertilizer_id=1,
        )

    captured = capsys.readouterr()
    assert "COLETA FAOSTAT PREÇOS CONCLUÍDA COM SUCESSO!" in captured.out
    assert "Filtro de fertilizante: Ureia (ID 1)" in captured.out


# ==============================================================================
# 10. TESTE DE BOOTSTRAP: Execução direta com Python do Sistema
# ==============================================================================

def test_cli_scripts_execute_via_system_python_without_modulenotfound():
    """Comportamento: Quando o usuário executa 'python scripts/...' no terminal sem ativar a venv, o bootstrap deve delegar para a .venv e não lançar ModuleNotFoundError."""
    import subprocess
    import sys

    # Executa com python.exe do sistema (ou sys.executable atual)
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "collect_benchmark_prices.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "ModuleNotFoundError" not in proc.stderr
    assert "usage:" in proc.stdout.lower() or "uso:" in proc.stdout.lower()



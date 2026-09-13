"""Testes unitários rigorosos para execução de ferramentas agronômicas e de mercado."""

import pandas as pd
from unittest.mock import patch
import pytest

from app.application.use_cases.ai.tool_executor import ToolExecutor


class TestToolExecutorStrict:
    """Validação estrita de cada uma das ferramentas de dados reais do FertiPartner."""

    def test_unknown_tool_dispatch(self):
        res = ToolExecutor.execute("invalid_tool_name_xyz", {})
        assert "error" in res
        assert "Ferramenta desconhecida" in res["error"]

    def test_tool_exception_wrapped_cleanly(self):
        with patch.object(ToolExecutor, "_tool_get_fertilizer_technical_spec", side_effect=ValueError("Test crash")):
            res = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "Ureia"})
            assert "error" in res
            assert "Erro na execução da ferramenta" in res["error"]

    def test_get_fertilizer_technical_spec_success_and_accents(self):
        # Consulta com acento e minúsculas
        res = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "ureia"})
        assert res["status"] == "success"
        assert res["fertilizer_name"] == "Ureia"
        assert res["chemical_formula"] == "CO(NH2)2"
        assert "CO(NH2)2" in res["chemical_formula"]
        assert "typical_nutrients" in res or "guarantees" in res

        # Consulta com sigla MAP
        res_map = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "map"})
        assert res_map["status"] == "success"
        assert "Fosfato Monoamônico" in res_map["fertilizer_name"] or "MAP" in res_map["fertilizer_name"]

    def test_get_fertilizer_technical_spec_not_found(self):
        res = ToolExecutor.execute("get_fertilizer_technical_spec", {"fertilizer_name": "ProdutoInexistente999"})
        assert res["status"] == "not_found"
        assert "não encontrado no catálogo" in res["message"]

    def test_get_price_trends_tool(self):
        sample_df = pd.DataFrame([
            {
                "fertilizer_id": 1,
                "fertilizer_name": "Ureia",
                "price_date": "2024-01-01",
                "benchmark_name": "Ureia Granulada CFR Brasil",
                "incoterm": "CFR",
                "standard_price_usd_per_mt": 365.50,
                "month_over_month_pct_change": 2.5,
            }
        ])
        with patch("app.application.use_cases.ai.tool_executor.FertiDataService.get_price_benchmark_trends", return_value=sample_df):
            res = ToolExecutor.execute("get_price_trends", {"fertilizer_name": "Ureia"})
            assert res["status"] == "success"
            assert res["total_records"] >= 1
            assert len(res["recent_prices"]) >= 1
            assert res["recent_prices"][0]["price_usd_per_mt"] == 365.50

    def test_get_trade_and_import_flows_tool(self):
        sample_df = pd.DataFrame([
            {
                "fertilizer_name": "Ureia",
                "exporter_country": "Rússia",
                "importer_country": "Brasil",
                "total_quantity_mt": 1500000.0,
                "total_value_usd": 500000000.0,
                "avg_usd_per_mt": 333.33,
            }
        ])
        with patch("app.application.use_cases.ai.tool_executor.FertiDataService.get_bilateral_trade_flows", return_value=sample_df):
            res = ToolExecutor.execute("get_trade_and_import_flows", {"fertilizer_name": "Ureia"})
            assert res["status"] == "success"
            assert len(res["top_trade_flows"]) == 1
            flow = res["top_trade_flows"][0]
            assert flow["exporter"] == "Rússia"
            assert flow["importer"] == "Brasil"
            assert flow["volume_mt"] == 1500000.0

    def test_get_brazil_supply_balance_tool(self):
        sample_df = pd.DataFrame([
            {
                "fertilizer_name": "Fosfato Diamônico (DAP)",
                "ref_year": 2024,
                "apparent_consumption_mt": 400000.0,
                "national_production_mt": 0.0,
                "total_imports_mt": 400000.0,
                "external_dependency_pct": 100.0,
            }
        ])
        with patch("app.application.use_cases.ai.tool_executor.FertiDataService.get_brazil_external_dependency", return_value=sample_df):
            res = ToolExecutor.execute("get_brazil_supply_balance", {"fertilizer_name": "DAP"})
            assert res["status"] == "success"
            assert len(res["brazil_balances"]) == 1
            balance = res["brazil_balances"][0]
            assert balance["national_production_mt"] == 0.0
            assert balance["external_dependency_pct"] == 100.0
            assert balance["apparent_consumption_mt"] == 400000.0

    def test_get_recent_news_and_sentiment_tools(self):
        news_df = pd.DataFrame([
            {
                "title": "Porto de Paranaguá bate recorde de descarga de fertilizantes",
                "source": "Canal Rural",
                "pub_date_relative": "Há 2 dias",
                "topic": "FRETE / LOGÍSTICA",
                "nutrient": "Todos",
                "snippet": "Movimentação recorde de fertilizantes nitrogenados e fosfatados nos berços preferenciais.",
            }
        ])
        sentiment_list = [
            {
                "topic": "FRETE / LOGÍSTICA",
                "short_name": "Logística",
                "score": 4.5,
                "classification": "Melhorando",
                "status_label": "Fluidez Normal",
                "news_count": 10,
            }
        ]

        with patch("app.application.use_cases.ai.tool_executor.GoogleNewsService.fetch_fertilizer_news", return_value=news_df), \
             patch("app.application.use_cases.ai.tool_executor.GoogleNewsService.analyze_sentiment_by_topic", return_value=sentiment_list):

            # 1. Test news tool
            res_news = ToolExecutor.execute("get_recent_news_7d", {"topic": "FRETE / LOGÍSTICA"})
            assert res_news["status"] == "success"
            assert res_news["total_news_found"] == 1
            assert "Paranaguá" in res_news["recent_articles"][0]["title"]

            # 2. Test sentiment tool
            res_sent = ToolExecutor.execute("get_market_sentiment_barometers", {})
            assert res_sent["status"] == "success"
            assert len(res_sent["market_barometers"]) == 1
            assert res_sent["market_barometers"][0]["classification"] == "Melhorando"

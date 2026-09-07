"""Executor de ferramentas (Tools) conectado às fontes de dados reais do FertiPartner."""

import unicodedata
from typing import Any
import pandas as pd

from domain.fertilizers import FERTILIZERS_CATALOG
from app.presentation.streamlit.services.data_service import FertiDataService
from app.presentation.streamlit.services.news_service import GoogleNewsService


def _normalize(s: str) -> str:
    """Normaliza texto para busca insensível a acentuação."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


class ToolExecutor:
    """Executa chamadas de ferramentas emitidas pelo Google Gemini."""

    @classmethod
    def execute(cls, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Despacha e executa a ferramenta solicitada."""
        method = getattr(cls, f"_tool_{tool_name}", None)
        if not method:
            return {"error": f"Ferramenta desconhecida: {tool_name}"}
        try:
            return method(args)
        except Exception as exc:
            return {"error": f"Erro na execução da ferramenta {tool_name}: {str(exc)}"}

    @classmethod
    def _find_fertilizer(cls, query_name: str) -> dict[str, Any] | None:
        """Localiza um fertilizante no catálogo pelo nome aproximado."""
        q = _normalize(query_name)
        for fert in FERTILIZERS_CATALOG:
            f_name = _normalize(fert.get("name", ""))
            slug = _normalize(fert.get("slug", ""))
            synonyms = [_normalize(s) for s in fert.get("synonyms", [])]
            if q in f_name or q in slug or any(q in syn for syn in synonyms) or any(syn in q for syn in synonyms):
                return fert
        return None

    @classmethod
    def _tool_get_fertilizer_technical_spec(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna a ficha técnica agronômica detalhada."""
        fert_name = args.get("fertilizer_name", "")
        fert = cls._find_fertilizer(fert_name)
        if not fert:
            return {"status": "not_found", "message": f"Fertilizante '{fert_name}' não encontrado no catálogo oficial."}

        return {
            "status": "success",
            "fertilizer_name": fert.get("canonical_name", fert.get("name")),
            "category": fert.get("category_name", fert.get("category")),
            "chemical_formula": fert.get("chemical_formula"),
            "ncm_code": fert.get("hs_ncm_codes", fert.get("ncm_code")),
            "cas_number": fert.get("cas_rn", fert.get("cas_number")),
            "guarantees": fert.get("typical_nutrients", fert.get("guarantees")),
            "physical_properties": fert.get("physical_properties"),
            "agronomic_usage": fert.get("agronomic_usage", fert.get("agronomic_description")),
            "handling_storage": fert.get("handling_storage", fert.get("storage_precautions")),
            "description": fert.get("detailed_description", fert.get("description")),
        }

    @classmethod
    def _tool_get_price_trends(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna as cotações históricas internacionais e no Brasil."""
        fert_name = args.get("fertilizer_name", "")
        fert = cls._find_fertilizer(fert_name)

        df_prices = FertiDataService.get_price_benchmark_trends()
        if df_prices.empty:
            return {"status": "no_data", "message": f"Sem cotações registradas para '{fert_name}'."}

        if fert:
            f_canon = fert.get("canonical_name", fert.get("name", ""))
            f_norm = _normalize(f_canon)
            mask = df_prices["fertilizer_name"].apply(lambda x: f_norm in _normalize(str(x)) or _normalize(str(x)) in f_norm)
            if mask.any():
                df_prices = df_prices[mask]

        # Converte últimos registros em registros de leitura rápida
        recent_records = []
        for _, row in df_prices.tail(8).iterrows():
            recent_records.append({
                "date": str(row.get("price_date", "")),
                "benchmark": row.get("benchmark_name", ""),
                "incoterm": row.get("incoterm", ""),
                "price_usd_per_mt": float(row.get("standard_price_usd_per_mt", 0.0)),
                "mom_pct_change": float(row.get("month_over_month_pct_change", 0.0)),
            })

        return {
            "status": "success",
            "fertilizer_consulted": fert.get("name") if fert else fert_name,
            "total_records": len(df_prices),
            "recent_prices": recent_records,
        }

    @classmethod
    def _tool_get_trade_and_import_flows(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna os fluxos reais de comércio exterior."""
        fert_name = args.get("fertilizer_name", "")
        fert = cls._find_fertilizer(fert_name)

        df_trade = FertiDataService.get_bilateral_trade_flows()
        if df_trade.empty:
            return {"status": "no_data", "message": "Nenhum fluxo comercial encontrado para os critérios."}

        if fert:
            f_canon = fert.get("canonical_name", fert.get("name", ""))
            f_norm = _normalize(f_canon)
            mask = df_trade["fertilizer_name"].apply(lambda x: f_norm in _normalize(str(x)) or _normalize(str(x)) in f_norm)
            if mask.any():
                df_trade = df_trade[mask]

        top_flows = []
        for _, row in df_trade.head(10).iterrows():
            top_flows.append({
                "fertilizer": row.get("fertilizer_name", ""),
                "exporter": row.get("exporter_country", ""),
                "importer": row.get("importer_country", ""),
                "volume_mt": float(row.get("total_quantity_mt", 0.0)),
                "value_usd": float(row.get("total_value_usd", 0.0)),
                "avg_usd_mt": float(row.get("avg_usd_per_mt", 0.0)),
            })

        return {
            "status": "success",
            "top_trade_flows": top_flows,
        }

    @classmethod
    def _tool_get_brazil_supply_balance(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna o balanço físico e dependência externa brasileira."""
        fert_name = args.get("fertilizer_name", "")
        fert = cls._find_fertilizer(fert_name) if fert_name else None

        df_dep = FertiDataService.get_brazil_external_dependency()
        if df_dep.empty:
            return {"status": "no_data", "message": "Dados de balanço nacional não disponíveis."}

        if fert:
            f_canon = fert.get("canonical_name", fert.get("name", ""))
            f_norm = _normalize(f_canon)
            mask = df_dep["fertilizer_name"].apply(lambda x: f_norm in _normalize(str(x)) or _normalize(str(x)) in f_norm)
            if mask.any():
                df_dep = df_dep[mask]

        balances = []
        for _, row in df_dep.iterrows():
            balances.append({
                "fertilizer": row.get("fertilizer_name", ""),
                "year": int(row.get("ref_year", 2024)),
                "apparent_consumption_mt": float(row.get("apparent_consumption_mt", 0.0)) if pd.notna(row.get("apparent_consumption_mt")) else 0.0,
                "national_production_mt": float(row.get("national_production_mt", 0.0)) if pd.notna(row.get("national_production_mt")) else 0.0,
                "total_imports_mt": float(row.get("total_imports_mt", 0.0)) if pd.notna(row.get("total_imports_mt")) else 0.0,
                "external_dependency_pct": float(row.get("external_dependency_pct", 0.0)) if pd.notna(row.get("external_dependency_pct")) else 0.0,
            })

        return {
            "status": "success",
            "brazil_balances": balances,
        }

    @classmethod
    def _tool_get_recent_news_7d(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna matérias dos últimos 7 dias."""
        df_news = GoogleNewsService.fetch_fertilizer_news()
        if df_news.empty:
            return {"status": "no_news", "message": "Nenhuma notícia capturada nos últimos 7 dias."}

        topic_filter = args.get("topic")
        if topic_filter and topic_filter != "TODOS":
            df_news = df_news[df_news["topic"] == topic_filter]

        recent_items = []
        for _, row in df_news.head(8).iterrows():
            recent_items.append({
                "title": row.get("title", ""),
                "source": row.get("source", ""),
                "published_relative": row.get("pub_date_relative", ""),
                "topic": row.get("topic", ""),
                "nutrient": row.get("nutrient", ""),
                "snippet": row.get("snippet", "")[:180],
            })

        return {
            "status": "success",
            "total_news_found": len(df_news),
            "recent_articles": recent_items,
        }

    @classmethod
    def _tool_get_market_sentiment_barometers(cls, args: dict[str, Any]) -> dict[str, Any]:
        """Retorna os barômetros de sentimento setorial calculados."""
        df_news = GoogleNewsService.fetch_fertilizer_news()
        sentiments = GoogleNewsService.analyze_sentiment_by_topic(df_news)

        formatted = []
        for s in sentiments:
            formatted.append({
                "topic": s.get("topic", ""),
                "short_name": s.get("short_name", ""),
                "sentiment_score": s.get("score", ""),
                "classification": s.get("classification", ""),
                "status_label": s.get("status_label", ""),
                "news_analyzed": s.get("news_count", 0),
            })

        return {
            "status": "success",
            "market_barometers": formatted,
        }

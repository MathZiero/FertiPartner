"""Serviço de dados analíticos para o Streamlit com cache e fallback resiliente."""

import logging
from typing import Any, cast
import pandas as pd
import streamlit as st

from app.infrastructure.supabase.client import SupabaseClientManager

logger = logging.getLogger(__name__)


# ==============================================================================
# FALLBACK MOCK DATA (Garante funcionamento offline e em testes sem conexão)
# ==============================================================================

from domain.fertilizers import FERTILIZERS_CATALOG

# Alias para manter total retrocompatibilidade
MOCK_FERTILIZERS = FERTILIZERS_CATALOG

MOCK_GLOBAL_PRODUCTION = [
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "country_id": 2, "country_name": "China", "country_iso3": "CHN", "production_year": 2023, "standard_quantity_mt": 58200000.0, "global_total_mt": 79100000.0, "global_market_share_pct": 73.58, "rank_position": 1},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "country_id": 3, "country_name": "Índia", "country_iso3": "IND", "production_year": 2023, "standard_quantity_mt": 12500000.0, "global_total_mt": 79100000.0, "global_market_share_pct": 15.80, "rank_position": 2},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "country_id": 5, "country_name": "Rússia", "country_iso3": "RUS", "production_year": 2023, "standard_quantity_mt": 4800000.0, "global_total_mt": 79100000.0, "global_market_share_pct": 6.07, "rank_position": 3},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "country_id": 1, "country_name": "Brasil", "country_iso3": "BRA", "production_year": 2023, "standard_quantity_mt": 650000.0, "global_total_mt": 79100000.0, "global_market_share_pct": 0.82, "rank_position": 4},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "country_id": 6, "country_name": "Canadá", "country_iso3": "CAN", "production_year": 2023, "standard_quantity_mt": 22400000.0, "global_total_mt": 68500000.0, "global_market_share_pct": 32.70, "rank_position": 1},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "country_id": 5, "country_name": "Rússia", "country_iso3": "RUS", "production_year": 2023, "standard_quantity_mt": 14200000.0, "global_total_mt": 68500000.0, "global_market_share_pct": 20.73, "rank_position": 2},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "country_id": 8, "country_name": "Belarus", "country_iso3": "BLR", "production_year": 2023, "standard_quantity_mt": 9800000.0, "global_total_mt": 68500000.0, "global_market_share_pct": 14.31, "rank_position": 3},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "country_id": 2, "country_name": "China", "country_iso3": "CHN", "production_year": 2023, "standard_quantity_mt": 8200000.0, "global_total_mt": 68500000.0, "global_market_share_pct": 11.97, "rank_position": 4},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "country_id": 2, "country_name": "China", "country_iso3": "CHN", "production_year": 2023, "standard_quantity_mt": 18500000.0, "global_total_mt": 36000000.0, "global_market_share_pct": 51.39, "rank_position": 1},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "country_id": 7, "country_name": "Marrocos", "country_iso3": "MAR", "production_year": 2023, "standard_quantity_mt": 7200000.0, "global_total_mt": 36000000.0, "global_market_share_pct": 20.00, "rank_position": 2},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "country_id": 5, "country_name": "Rússia", "country_iso3": "RUS", "production_year": 2023, "standard_quantity_mt": 4500000.0, "global_total_mt": 36000000.0, "global_market_share_pct": 12.50, "rank_position": 3},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "country_id": 4, "country_name": "Estados Unidos", "country_iso3": "USA", "production_year": 2023, "standard_quantity_mt": 3100000.0, "global_total_mt": 36000000.0, "global_market_share_pct": 8.61, "rank_position": 4},
]

MOCK_BRAZIL_DEPENDENCY = [
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "ref_year": 2024, "national_production_mt": 650000.0, "total_imports_mt": 7120000.0, "total_exports_mt": 12000.0, "apparent_consumption_mt": 7758000.0, "external_dependency_pct": 91.78},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "ref_year": 2024, "national_production_mt": 1250000.0, "total_imports_mt": 4890000.0, "total_exports_mt": 5000.0, "apparent_consumption_mt": 6135000.0, "external_dependency_pct": 79.71},
    {"fertilizer_id": 3, "fertilizer_name": "Fosfato Diamônico (DAP)", "ref_year": 2024, "national_production_mt": 320000.0, "total_imports_mt": 1650000.0, "total_exports_mt": 2000.0, "apparent_consumption_mt": 1968000.0, "external_dependency_pct": 83.84},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "ref_year": 2024, "national_production_mt": 380000.0, "total_imports_mt": 12850000.0, "total_exports_mt": 0.0, "apparent_consumption_mt": 13230000.0, "external_dependency_pct": 97.13},
    {"fertilizer_id": 7, "fertilizer_name": "Sulfato de Amônio", "ref_year": 2024, "national_production_mt": 420000.0, "total_imports_mt": 3950000.0, "total_exports_mt": 1500.0, "apparent_consumption_mt": 4368500.0, "external_dependency_pct": 90.42},
]

MOCK_TRADE_FLOWS = [
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "flow_type": "IMPORT", "exporter_country": "Canadá", "exporter_iso3": "CAN", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 4820000.0, "total_value_usd": 1783400000.0, "avg_usd_per_mt": 370.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "flow_type": "IMPORT", "exporter_country": "Rússia", "exporter_iso3": "RUS", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 3650000.0, "total_value_usd": 1295750000.0, "avg_usd_per_mt": 355.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "flow_type": "IMPORT", "exporter_country": "Belarus", "exporter_iso3": "BLR", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 1950000.0, "total_value_usd": 682500000.0, "avg_usd_per_mt": 350.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "flow_type": "IMPORT", "exporter_country": "Rússia", "exporter_iso3": "RUS", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 2450000.0, "total_value_usd": 955500000.0, "avg_usd_per_mt": 390.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "flow_type": "IMPORT", "exporter_country": "Catar", "exporter_iso3": "QAT", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 1820000.0, "total_value_usd": 728000000.0, "avg_usd_per_mt": 400.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "flow_type": "IMPORT", "exporter_country": "Omã", "exporter_iso3": "OMN", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 1210000.0, "total_value_usd": 484000000.0, "avg_usd_per_mt": 400.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "flow_type": "IMPORT", "exporter_country": "Marrocos", "exporter_iso3": "MAR", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 2100000.0, "total_value_usd": 1281000000.0, "avg_usd_per_mt": 610.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "flow_type": "IMPORT", "exporter_country": "Rússia", "exporter_iso3": "RUS", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 1850000.0, "total_value_usd": 1110000000.0, "avg_usd_per_mt": 600.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "flow_type": "IMPORT", "exporter_country": "Arábia Saudita", "exporter_iso3": "SAU", "importer_country": "Brasil", "importer_iso3": "BRA", "trade_year": 2023, "total_quantity_mt": 940000.0, "total_value_usd": 573400000.0, "avg_usd_per_mt": 610.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "flow_type": "IMPORT", "exporter_country": "China", "exporter_iso3": "CHN", "importer_country": "Índia", "importer_iso3": "IND", "trade_year": 2023, "total_quantity_mt": 3400000.0, "total_value_usd": 1360000000.0, "avg_usd_per_mt": 400.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "flow_type": "IMPORT", "exporter_country": "Canadá", "exporter_iso3": "CAN", "importer_country": "Estados Unidos", "importer_iso3": "USA", "trade_year": 2023, "total_quantity_mt": 8500000.0, "total_value_usd": 3145000000.0, "avg_usd_per_mt": 370.0},
]

MOCK_PRICE_TRENDS = [
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 1, "benchmark_name": "Ureia Granulada FOB Mar Báltico", "hub_port_name": "Portos do Báltico", "incoterm": "FOB", "price_date": "2023-01-01", "standard_price_usd_per_mt": 485.0, "month_over_month_pct_change": -5.2, "moving_avg_3m_usd": 510.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 1, "benchmark_name": "Ureia Granulada FOB Mar Báltico", "hub_port_name": "Portos do Báltico", "incoterm": "FOB", "price_date": "2023-04-01", "standard_price_usd_per_mt": 360.0, "month_over_month_pct_change": -8.1, "moving_avg_3m_usd": 405.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 1, "benchmark_name": "Ureia Granulada FOB Mar Báltico", "hub_port_name": "Portos do Báltico", "incoterm": "FOB", "price_date": "2023-08-01", "standard_price_usd_per_mt": 415.0, "month_over_month_pct_change": 12.3, "moving_avg_3m_usd": 385.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 1, "benchmark_name": "Ureia Granulada FOB Mar Báltico", "hub_port_name": "Portos do Báltico", "incoterm": "FOB", "price_date": "2023-12-01", "standard_price_usd_per_mt": 380.0, "month_over_month_pct_change": -2.4, "moving_avg_3m_usd": 395.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 3, "benchmark_name": "Ureia Granulada CFR Portos Brasileiros", "hub_port_name": "Paranaguá / Santos", "incoterm": "CFR", "price_date": "2023-01-01", "standard_price_usd_per_mt": 535.0, "month_over_month_pct_change": -4.8, "moving_avg_3m_usd": 560.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 3, "benchmark_name": "Ureia Granulada CFR Portos Brasileiros", "hub_port_name": "Paranaguá / Santos", "incoterm": "CFR", "price_date": "2023-04-01", "standard_price_usd_per_mt": 410.0, "month_over_month_pct_change": -7.2, "moving_avg_3m_usd": 450.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 3, "benchmark_name": "Ureia Granulada CFR Portos Brasileiros", "hub_port_name": "Paranaguá / Santos", "incoterm": "CFR", "price_date": "2023-08-01", "standard_price_usd_per_mt": 465.0, "month_over_month_pct_change": 11.0, "moving_avg_3m_usd": 435.0},
    {"fertilizer_id": 1, "fertilizer_name": "Ureia", "benchmark_id": 3, "benchmark_name": "Ureia Granulada CFR Portos Brasileiros", "hub_port_name": "Paranaguá / Santos", "incoterm": "CFR", "price_date": "2023-12-01", "standard_price_usd_per_mt": 430.0, "month_over_month_pct_change": -2.1, "moving_avg_3m_usd": 445.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "benchmark_id": 7, "benchmark_name": "Cloreto de Potássio CFR Brasil", "hub_port_name": "Paranaguá", "incoterm": "CFR", "price_date": "2023-01-01", "standard_price_usd_per_mt": 520.0, "month_over_month_pct_change": -3.5, "moving_avg_3m_usd": 550.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "benchmark_id": 7, "benchmark_name": "Cloreto de Potássio CFR Brasil", "hub_port_name": "Paranaguá", "incoterm": "CFR", "price_date": "2023-06-01", "standard_price_usd_per_mt": 360.0, "month_over_month_pct_change": -4.2, "moving_avg_3m_usd": 380.0},
    {"fertilizer_id": 4, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "benchmark_id": 7, "benchmark_name": "Cloreto de Potássio CFR Brasil", "hub_port_name": "Paranaguá", "incoterm": "CFR", "price_date": "2023-12-01", "standard_price_usd_per_mt": 330.0, "month_over_month_pct_change": -1.5, "moving_avg_3m_usd": 340.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "benchmark_id": 5, "benchmark_name": "DAP FOB Marrocos", "hub_port_name": "Jorf Lasfar", "incoterm": "FOB", "price_date": "2023-01-01", "standard_price_usd_per_mt": 680.0, "month_over_month_pct_change": -2.0, "moving_avg_3m_usd": 700.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "benchmark_id": 5, "benchmark_name": "DAP FOB Marrocos", "hub_port_name": "Jorf Lasfar", "incoterm": "FOB", "price_date": "2023-06-01", "standard_price_usd_per_mt": 540.0, "month_over_month_pct_change": -3.8, "moving_avg_3m_usd": 570.0},
    {"fertilizer_id": 2, "fertilizer_name": "Fosfato Monoamônico (MAP)", "benchmark_id": 5, "benchmark_name": "DAP FOB Marrocos", "hub_port_name": "Jorf Lasfar", "incoterm": "FOB", "price_date": "2023-12-01", "standard_price_usd_per_mt": 595.0, "month_over_month_pct_change": 4.1, "moving_avg_3m_usd": 580.0},
]

MOCK_BRAZIL_UF_DATA = [
    {"uf": "MT", "state_name": "Mato Grosso", "share_pct": 28.5, "quantity_mt": 12800000.0},
    {"uf": "PR", "state_name": "Paraná", "share_pct": 14.2, "quantity_mt": 6380000.0},
    {"uf": "RS", "state_name": "Rio Grande do Sul", "share_pct": 11.8, "quantity_mt": 5300000.0},
    {"uf": "GO", "state_name": "Goiás", "share_pct": 10.4, "quantity_mt": 4670000.0},
    {"uf": "MG", "state_name": "Minas Gerais", "share_pct": 9.1, "quantity_mt": 4090000.0},
    {"uf": "SP", "state_name": "São Paulo", "share_pct": 8.6, "quantity_mt": 3860000.0},
    {"uf": "MS", "state_name": "Mato Grosso do Sul", "share_pct": 7.3, "quantity_mt": 3280000.0},
    {"uf": "BA", "state_name": "Bahia", "share_pct": 5.2, "quantity_mt": 2340000.0},
    {"uf": "OUTROS", "state_name": "Demais Estados", "share_pct": 4.9, "quantity_mt": 2200000.0},
]

MOCK_AUDIT_RUNS = [
    {"source_name": "Comex Stat (MDIC)", "source_code": "COMEXSTAT_IMP", "status": "COMPLETED", "records_count": 4820, "started_at": "2026-09-02 20:30:00", "execution_time_sec": 4.2},
    {"source_name": "UN Comtrade", "source_code": "UN_COMTRADE", "status": "COMPLETED", "records_count": 1250, "started_at": "2026-09-02 20:35:12", "execution_time_sec": 8.6},
    {"source_name": "FRED Economic Data", "source_code": "FRED_FERT_PRICES", "status": "COMPLETED", "records_count": 340, "started_at": "2026-09-02 20:40:05", "execution_time_sec": 2.1},
    {"source_name": "FAOSTAT (FAO)", "source_code": "FAOSTAT_RFB", "status": "COMPLETED", "records_count": 890, "started_at": "2026-09-02 20:45:22", "execution_time_sec": 6.7},
]


# ==============================================================================
# DATA ACCESS SERVICE CLASS
# ==============================================================================

class FertiDataService:
    """Serviço unificado de acesso às views analíticas do FertiPartner com caching."""

    @staticmethod
    def _get_client():
        """Obtém o cliente Supabase de forma segura (admin se disponível para leitura irrestrita, senão público)."""
        try:
            return SupabaseClientManager.get_admin_client()
        except Exception:
            try:
                return SupabaseClientManager.get_client()
            except Exception as exc:
                logger.warning("Supabase não acessível diretamente: %s", exc)
                return None

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def check_connection(cls) -> bool:
        """Verifica se a conexão com o Supabase está ativa e operacional."""
        client = cls._get_client()
        if client is None:
            return False
        try:
            res = client.table("fertilizers").select("id").limit(1).execute()
            return res.data is not None
        except Exception:
            return False

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_fertilizer_profiles(cls) -> pd.DataFrame:
        """Obtém perfis de fertilizantes (fórmula, CAS, teores nutricionais, sinônimos)."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_fertilizer_profiles").select("*").execute()
                if res.data:
                    return pd.DataFrame(res.data)
            except Exception as exc:
                logger.warning("Falha ao buscar v_fertilizer_profiles: %s", exc)
        return pd.DataFrame(MOCK_FERTILIZERS)

    @classmethod
    def _build_fallback_production_rankings(cls) -> pd.DataFrame:
        """Constrói ranking completo a partir dos benchmarks homologados de produção."""
        try:
            from domain.benchmarks import PRODUCTION_BENCHMARKS
            iso_map = {
                "CN": ("China", "CHN", 2),
                "IN": ("Índia", "IND", 3),
                "RU": ("Rússia", "RUS", 5),
                "US": ("Estados Unidos", "USA", 4),
                "QA": ("Catar", "QAT", 9),
                "SA": ("Arábia Saudita", "SAU", 10),
                "EG": ("Egito", "EGY", 11),
                "CA": ("Canadá", "CAN", 6),
                "DE": ("Alemanha", "DEU", 12),
                "BR": ("Brasil", "BRA", 1),
                "MA": ("Marrocos", "MAR", 7),
                "BY": ("Belarus", "BLR", 8),
                "TT": ("Trinidad e Tobago", "TTO", 13),
            }
            fert_names = {f["id"]: f["canonical_name"] for f in FERTILIZERS_CATALOG}
            rows = []
            for item in PRODUCTION_BENCHMARKS:
                fid = item["fert_id"]
                fname = fert_names.get(fid, f"Fertilizante {fid}")
                c_name, c_iso3, cid = iso_map.get(item["iso2"], (item["iso2"], item["iso2"], 99))
                for y, qty in item["years"].items():
                    rows.append({
                        "fertilizer_id": fid,
                        "fertilizer_name": fname,
                        "country_id": cid,
                        "country_name": c_name,
                        "country_iso3": c_iso3,
                        "production_year": int(y),
                        "standard_quantity_mt": float(qty),
                    })
            if rows:
                df = pd.DataFrame(rows)
                totals = df.groupby(["fertilizer_id", "production_year"])["standard_quantity_mt"].transform("sum")
                df["global_total_mt"] = totals
                df["global_market_share_pct"] = (df["standard_quantity_mt"] / df["global_total_mt"] * 100).round(2)
                df["rank_position"] = df.groupby(["fertilizer_id", "production_year"])["standard_quantity_mt"].rank(ascending=False, method="min").astype(int)
                return df
        except Exception as exc:
            logger.warning("Falha ao construir fallback de produção dinâmico: %s", exc)
        return pd.DataFrame(MOCK_GLOBAL_PRODUCTION)

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_global_production_rankings(cls) -> pd.DataFrame:
        """Obtém o ranking de produção global por país, ano e fertilizante."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_global_production_rankings").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    for col in ["standard_quantity_mt", "global_total_mt", "global_market_share_pct", "rank_position"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    return df
            except Exception as exc:
                logger.warning("Falha ao buscar v_global_production_rankings: %s", exc)
        return cls._build_fallback_production_rankings()

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_bilateral_trade_flows(cls) -> pd.DataFrame:
        """Obtém os fluxos bilaterais de comércio exterior (Sankey e mapas)."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_bilateral_trade_flows").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    for col in ["total_quantity_mt", "total_value_usd", "avg_usd_per_mt", "trade_year"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    return df
            except Exception as exc:
                logger.warning("Falha ao buscar v_bilateral_trade_flows: %s", exc)
        return pd.DataFrame(MOCK_TRADE_FLOWS)

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_brazil_external_dependency(cls) -> pd.DataFrame:
        """Obtém indicadores de consumo aparente e taxa de dependência externa do Brasil com proteção sistêmica contra dados incompletos."""
        client = cls._get_client()
        df = None
        if client:
            try:
                res = client.table("v_brazil_external_dependency").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
            except Exception as exc:
                logger.warning("Falha ao buscar v_brazil_external_dependency: %s", exc)

        if df is None or df.empty:
            df = pd.DataFrame(MOCK_BRAZIL_DEPENDENCY)

        for col in ["national_production_mt", "total_imports_mt", "total_exports_mt", "apparent_consumption_mt", "external_dependency_pct", "ref_year"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Proteção sistêmica contra assimetria temporal:
        # Quando produção for nula/ausente para um ano onde há importações, não inventa 0 nem distorce dependência
        if "data_status" not in df.columns:
            has_prod = df["national_production_mt"].notna() & (df["national_production_mt"] > 0)
            has_import = df["total_imports_mt"].notna() & (df["total_imports_mt"] > 0)
            df["is_consolidated"] = has_prod & has_import
            df["data_status"] = df["is_consolidated"].map({True: "CONSOLIDATED", False: "PENDING_PRODUCTION"})
        else:
            df["is_consolidated"] = df["data_status"] == "CONSOLIDATED"

        # Se a produção não estiver consolidada, zera os cálculos derivados espúrios
        mask_incomplete = ~df["is_consolidated"]
        df.loc[mask_incomplete, "apparent_consumption_mt"] = None
        df.loc[mask_incomplete, "external_dependency_pct"] = None

        return df

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_database_consistency_matrix(cls) -> pd.DataFrame:
        """Retorna matriz de consistência temporal e sincronismo do banco de dados (Trade vs Produção vs Preços)."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_data_consistency_matrix").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    for col in ["ref_year", "trade_records_count", "prod_records_count", "producing_countries_count", "price_points_count"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    return df
            except Exception as exc:
                logger.debug("View v_data_consistency_matrix ainda não migrada (%s). Computando via tabelas base...", exc)

            try:
                res_t = client.table("trade_records").select("fertilizer_id, period_start_date").execute()
                res_p = client.table("production_records").select("fertilizer_id, period_start_date, country_id").execute()
                res_pr = client.table("price_records").select("fertilizer_id, price_date").execute()
                res_f = client.table("fertilizers").select("id, canonical_name").execute()

                fert_map = {f["id"]: f["canonical_name"] for f in (res_f.data or [])}
                years = {2022, 2023, 2024}
                for t in (res_t.data or []):
                    if t.get("period_start_date"):
                        years.add(int(str(t["period_start_date"])[:4]))
                for p in (res_p.data or []):
                    if p.get("period_start_date"):
                        years.add(int(str(p["period_start_date"])[:4]))
                for pr in (res_pr.data or []):
                    if pr.get("price_date"):
                        years.add(int(str(pr["price_date"])[:4]))

                rows = []
                for y in sorted(years):
                    for fid, fname in fert_map.items():
                        t_count = sum(1 for t in (res_t.data or []) if t.get("fertilizer_id") == fid and str(t.get("period_start_date", ""))[:4] == str(y))
                        p_recs = [p for p in (res_p.data or []) if p.get("fertilizer_id") == fid and str(p.get("period_start_date", ""))[:4] == str(y)]
                        pr_count = sum(1 for pr in (res_pr.data or []) if pr.get("fertilizer_id") == fid and str(pr.get("price_date", ""))[:4] == str(y))

                        prod_count = len(p_recs)
                        prod_countries = len({p.get("country_id") for p in p_recs if p.get("country_id")})

                        if t_count + prod_count + pr_count == 0:
                            continue

                        if t_count > 0 and prod_count > 0 and pr_count > 0:
                            status = "FULLY_SYNCHRONIZED"
                        elif t_count > 0 and prod_count == 0:
                            status = "AWAITING_PRODUCTION_SURVEY"
                        elif t_count == 0 and prod_count > 0:
                            status = "AWAITING_TRADE_DATA"
                        else:
                            status = "PARTIAL_DATA"

                        rows.append({
                            "ref_year": y,
                            "fertilizer_id": fid,
                            "fertilizer_name": fname,
                            "trade_records_count": t_count,
                            "prod_records_count": prod_count,
                            "producing_countries_count": prod_countries,
                            "price_points_count": pr_count,
                            "synchronization_status": status,
                        })
                if rows:
                    return pd.DataFrame(rows)
            except Exception as exc2:
                logger.warning("Falha ao gerar matriz de consistência dinâmica: %s", exc2)

        return pd.DataFrame([
            {"ref_year": 2022, "fertilizer_name": "Ureia", "trade_records_count": 48, "prod_records_count": 13, "producing_countries_count": 13, "price_points_count": 12, "synchronization_status": "FULLY_SYNCHRONIZED"},
            {"ref_year": 2023, "fertilizer_name": "Ureia", "trade_records_count": 52, "prod_records_count": 13, "producing_countries_count": 13, "price_points_count": 12, "synchronization_status": "FULLY_SYNCHRONIZED"},
            {"ref_year": 2024, "fertilizer_name": "Ureia", "trade_records_count": 50, "prod_records_count": 13, "producing_countries_count": 13, "price_points_count": 12, "synchronization_status": "FULLY_SYNCHRONIZED"},
            {"ref_year": 2023, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "trade_records_count": 45, "prod_records_count": 8, "producing_countries_count": 8, "price_points_count": 12, "synchronization_status": "FULLY_SYNCHRONIZED"},
            {"ref_year": 2024, "fertilizer_name": "Cloreto de Potássio (KCl / MOP)", "trade_records_count": 42, "prod_records_count": 8, "producing_countries_count": 8, "price_points_count": 12, "synchronization_status": "FULLY_SYNCHRONIZED"},
        ])


    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_price_benchmark_trends(cls) -> pd.DataFrame:
        """Obtém séries históricas de preços com médias móveis e variações percentuais."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_price_benchmark_trends").select("*").order("price_date").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    for col in ["standard_price_usd_per_mt", "prev_price_usd_per_mt", "month_over_month_pct_change", "moving_avg_3m_usd"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    if "price_date" in df.columns:
                        df["price_date"] = pd.to_datetime(df["price_date"])
                    return df
            except Exception as exc:
                logger.warning("Falha ao buscar v_price_benchmark_trends: %s", exc)
        df_mock = pd.DataFrame(MOCK_PRICE_TRENDS)
        df_mock["price_date"] = pd.to_datetime(df_mock["price_date"])
        return df_mock

    @classmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def get_brazil_uf_distribution(cls) -> pd.DataFrame:
        """Obtém estimativa e distribuição do consumo/entrega de fertilizantes por estado (UF)."""
        client = cls._get_client()
        if client:
            try:
                # Consulta aos detalhes de Comex do Brasil
                res = client.table("brazil_trade_details").select("brazilian_state_uf").execute()
                if res.data:
                    df_uf = pd.DataFrame(res.data)
                    if not df_uf.empty and "brazilian_state_uf" in df_uf.columns:
                        counts = df_uf["brazilian_state_uf"].value_counts().reset_index()
                        counts.columns = ["uf", "records"]
                        counts["share_pct"] = (counts["records"] / counts["records"].sum()) * 100
                        # Mapeamento do nome completo dos estados
                        uf_names = {
                            "MT": "Mato Grosso", "PR": "Paraná", "RS": "Rio Grande do Sul",
                            "GO": "Goiás", "MG": "Minas Gerais", "SP": "São Paulo",
                            "MS": "Mato Grosso do Sul", "BA": "Bahia", "SC": "Santa Catarina",
                            "MA": "Maranhão", "PA": "Pará", "RJ": "Rio de Janeiro",
                        }
                        counts["state_name"] = counts["uf"].map(uf_names).fillna("Outros Estados")
                        counts["quantity_mt"] = counts["records"] * 100000.0  # estimativa relativa
                        return counts
            except Exception as exc:
                logger.warning("Falha ao buscar brazil_trade_details: %s", exc)
        return pd.DataFrame(MOCK_BRAZIL_UF_DATA)

    @classmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_audit_runs(cls) -> pd.DataFrame:
        """Obtém histórico recente de execuções de coleta e integridade das fontes com cálculo de duração e metadados."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("data_collection_runs").select("*, data_sources(name, code)").order("started_at", desc=True).limit(30).execute()
                if res.data:
                    runs_data = cast(list[dict[str, Any]], res.data)
                    runs = []
                    for r in runs_data:
                        if not isinstance(r, dict):
                            continue
                        src = r.get("data_sources")
                        src_dict: dict[str, Any] = (
                            src if isinstance(src, dict)
                            else (src[0] if isinstance(src, list) and src and isinstance(src[0], dict) else {})
                        )
                        # Duração calculada entre started_at e finished_at
                        started = r.get("started_at")
                        finished = r.get("finished_at")
                        duration_sec = 0.0
                        if started and finished:
                            try:
                                t_start = pd.to_datetime(started)
                                t_finish = pd.to_datetime(finished)
                                duration_sec = max(0.0, (t_finish - t_start).total_seconds())
                            except Exception:
                                pass

                        # Tradução legível dos parâmetros e dados requisitados
                        meta = r.get("metadata") or {}
                        req_desc = "Carga padrão"
                        if isinstance(meta, dict) and meta:
                            parts = []
                            if "period" in meta:
                                parts.append(f"Período: {meta['period']}")
                            elif "year" in meta:
                                parts.append(f"Ano: {meta['year']}")
                            if "flow" in meta:
                                parts.append(f"Fluxo: {meta['flow'].upper()}")
                            if "top_n" in meta:
                                parts.append(f"Top {meta['top_n']}")
                            if "commodities" in meta:
                                parts.append(f"{len(meta['commodities'])} códigos HS")
                            if "reporters" in meta:
                                parts.append(f"{len(meta['reporters'])} declarantes")
                            if parts:
                                req_desc = " • ".join(parts)

                        runs.append({
                            "source_name": src_dict.get("name", "Fonte Oficial"),
                            "source_code": src_dict.get("code", "N/A"),
                            "requested_data": req_desc,
                            "status": r.get("status", "SUCCESS"),
                            "records_count": r.get("records_inserted", 0) or 0,
                            "records_fetched": r.get("records_fetched", 0) or 0,
                            "started_at": started,
                            "finished_at": finished,
                            "execution_time_sec": duration_sec,
                        })
                    return pd.DataFrame(runs)
            except Exception as exc:
                logger.warning("Falha ao buscar data_collection_runs: %s", exc)
        return pd.DataFrame(MOCK_AUDIT_RUNS)

    @classmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def get_sources_status(cls) -> pd.DataFrame:
        """Obtém status operacional, data de última ingestão e dados requisitados de cada fonte."""
        client = cls._get_client()
        if client:
            try:
                res_sources = client.table("data_sources").select("id, code, name, update_frequency, is_active").execute()
                res_runs = client.table("data_collection_runs").select("*").order("started_at", desc=True).limit(50).execute()

                sources = res_sources.data or []
                runs = res_runs.data or []

                latest_by_source: dict[int, dict[str, Any]] = {}
                for r in runs:
                    sid = r.get("source_id")
                    if sid and sid not in latest_by_source:
                        latest_by_source[sid] = r

                status_list = []
                for s in sources:
                    sid = s.get("id")
                    last_run = latest_by_source.get(sid)
                    last_time = last_run.get("started_at") if last_run else None
                    status = last_run.get("status") if last_run else ("Ativo" if s.get("is_active") else "Inativo")
                    inserted = last_run.get("records_inserted", 0) if last_run else 0

                    meta = last_run.get("metadata") if last_run else {}
                    req_desc = "Carga inicial agendada"
                    if meta and isinstance(meta, dict):
                        parts = []
                        if "period" in meta:
                            parts.append(f"Período: {meta['period']}")
                        elif "year" in meta:
                            parts.append(f"Ano: {meta['year']}")
                        if "flow" in meta:
                            parts.append(f"Fluxo: {meta['flow'].upper()}")
                        if "top_n" in meta:
                            parts.append(f"Top {meta['top_n']}")
                        if parts:
                            req_desc = " • ".join(parts)

                    status_list.append({
                        "source_name": s.get("name"),
                        "source_code": s.get("code"),
                        "frequency": s.get("update_frequency", "MENSAL"),
                        "last_ingestion": last_time or "Pendente de execução",
                        "last_status": status,
                        "records_inserted": inserted,
                        "requested_data": req_desc,
                    })
                if status_list:
                    return pd.DataFrame(status_list)
            except Exception as exc:
                logger.warning("Falha ao buscar status das fontes: %s", exc)

        # Fallback estruturado
        return pd.DataFrame([
            {"source_name": "MDIC Comex Stat", "source_code": "COMEXSTAT_IMP", "frequency": "MONTHLY", "last_ingestion": "2024-06-01", "last_status": "SUCCESS", "records_inserted": 1240, "requested_data": "Ano: 2024 • Fluxo: IMPORT"},
            {"source_name": "UN Comtrade API v1", "source_code": "UN_COMTRADE", "frequency": "MONTHLY", "last_ingestion": "2024-09-05", "last_status": "SUCCESS", "records_inserted": 4533, "requested_data": "Período: 2024 • Top 10"},
            {"source_name": "FAOSTAT Fertilizers", "source_code": "FAOSTAT_RFB", "frequency": "ANNUAL", "last_ingestion": "2024-09-05", "last_status": "SUCCESS", "records_inserted": 111, "requested_data": "Anos: 2022 a 2024 • Produção Mundial"},
            {"source_name": "FRED St. Louis Prices", "source_code": "FRED_FERT_PRICES", "frequency": "MONTHLY", "last_ingestion": "2024-09-02", "last_status": "SUCCESS", "records_inserted": 96, "requested_data": "Séries históricas de preços"},
        ])

    @classmethod
    def get_fertilizer_by_slug_or_id(cls, slug_or_id: str | int) -> dict[str, Any] | None:
        """Localiza o dicionário de especificações do fertilizante por slug ou ID."""
        for f in FERTILIZERS_CATALOG:
            if str(slug_or_id).isdigit():
                if f.get("id") == int(slug_or_id):
                    return f
            if f.get("slug") == str(slug_or_id).strip().lower():
                return f
        # Busca aproximada por canonical_name
        search = str(slug_or_id).lower()
        for f in FERTILIZERS_CATALOG:
            if search in f.get("canonical_name", "").lower():
                return f
        return None

    @classmethod
    def get_years_for_flow_type(cls, flow_type: str = "Produção", fertilizer_name: str | None = None) -> list[int]:
        """Retorna os anos disponíveis para o tipo de fluxo selecionado."""
        if flow_type == "Produção":
            df = cls.get_global_production_rankings()
            if not df.empty and "production_year" in df.columns:
                if fertilizer_name and fertilizer_name != "Todos":
                    df = df[df["fertilizer_name"].astype(str).str.contains(fertilizer_name, case=False, na=False) | (df["fertilizer_name"] == fertilizer_name)]
                years = sorted(df["production_year"].dropna().unique().astype(int).tolist(), reverse=True)
                if years:
                    return years
            return [2024, 2023, 2022]
        else:
            df = cls.get_bilateral_trade_flows()
            if not df.empty and "trade_year" in df.columns:
                if fertilizer_name and fertilizer_name != "Todos":
                    df = df[df["fertilizer_name"].astype(str).str.contains(fertilizer_name, case=False, na=False) | (df["fertilizer_name"] == fertilizer_name)]
                years = sorted(df["trade_year"].dropna().unique().astype(int).tolist(), reverse=True)
                if years:
                    return years
            return [2024, 2023, 2022]

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_global_map_data(
        cls,
        fertilizer_name: str | None = None,
        year: int | None = None,
        flow_type: str = "Produção",
    ) -> pd.DataFrame:
        """Obtém dados estruturados para o mapa global com suporte a Produção, Exportação e Importação."""
        if flow_type == "Produção":
            df = cls.get_global_production_rankings()
            if df.empty:
                return pd.DataFrame()
            df = df.copy()
            if fertilizer_name and fertilizer_name != "Todos":
                df = df[df["fertilizer_name"].astype(str).str.contains(fertilizer_name, case=False, na=False) | (df["fertilizer_name"] == fertilizer_name)]
            if year is not None and "production_year" in df.columns:
                df = df[df["production_year"] == year]
            df = df.rename(columns={"production_year": "ref_year"})
            return df
        elif flow_type == "Exportação":
            df_trade = cls.get_bilateral_trade_flows()
            if df_trade.empty:
                return pd.DataFrame()
            df_trade = df_trade.copy()
            if fertilizer_name and fertilizer_name != "Todos":
                df_trade = df_trade[df_trade["fertilizer_name"].astype(str).str.contains(fertilizer_name, case=False, na=False) | (df_trade["fertilizer_name"] == fertilizer_name)]
            if year is not None and "trade_year" in df_trade.columns:
                df_trade = df_trade[df_trade["trade_year"] == year]

            if df_trade.empty or "exporter_country" not in df_trade.columns:
                return pd.DataFrame()

            grouped = df_trade.groupby(["exporter_country", "exporter_iso3", "trade_year"], as_index=False).agg(
                standard_quantity_mt=("total_quantity_mt", "sum"),
                total_value_usd=("total_value_usd", "sum"),
            )
            total_exp = grouped["standard_quantity_mt"].sum()
            grouped["global_market_share_pct"] = (grouped["standard_quantity_mt"] / total_exp * 100) if total_exp > 0 else 0.0
            grouped = grouped.rename(columns={
                "exporter_country": "country_name",
                "exporter_iso3": "country_iso3",
                "trade_year": "ref_year",
            })
            grouped["rank_position"] = grouped["standard_quantity_mt"].rank(ascending=False, method="min").astype(int)
            return grouped
        elif flow_type == "Importação":
            df_trade = cls.get_bilateral_trade_flows()
            if df_trade.empty:
                return pd.DataFrame()
            df_trade = df_trade.copy()
            if fertilizer_name and fertilizer_name != "Todos":
                df_trade = df_trade[df_trade["fertilizer_name"].astype(str).str.contains(fertilizer_name, case=False, na=False) | (df_trade["fertilizer_name"] == fertilizer_name)]
            if year is not None and "trade_year" in df_trade.columns:
                df_trade = df_trade[df_trade["trade_year"] == year]

            if df_trade.empty or "importer_country" not in df_trade.columns:
                return pd.DataFrame()

            grouped = df_trade.groupby(["importer_country", "importer_iso3", "trade_year"], as_index=False).agg(
                standard_quantity_mt=("total_quantity_mt", "sum"),
                total_value_usd=("total_value_usd", "sum"),
            )
            total_imp = grouped["standard_quantity_mt"].sum()
            grouped["global_market_share_pct"] = (grouped["standard_quantity_mt"] / total_imp * 100) if total_imp > 0 else 0.0
            grouped = grouped.rename(columns={
                "importer_country": "country_name",
                "importer_iso3": "country_iso3",
                "trade_year": "ref_year",
            })
            grouped["rank_position"] = grouped["standard_quantity_mt"].rank(ascending=False, method="min").astype(int)
            return grouped
        return pd.DataFrame()



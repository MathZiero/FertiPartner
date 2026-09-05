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

MOCK_FERTILIZERS = [
    {
        "id": 1,
        "slug": "ureia",
        "canonical_name": "Ureia",
        "category_name": "Fertilizantes Nitrogenados",
        "chemical_formula": "CO(NH2)2",
        "cas_rn": "57-13-6",
        "description": "Fertilizante nitrogenado sólido de mais alta concentração (46% N), amplamente utilizado no mundo e no Brasil.",
        "typical_nutrients": {"N": 46.0},
        "synonyms": ["Carbamide", "Urea", "Ureia 46%"],
        "hs_ncm_codes": ["310210", "31021010"],
    },
    {
        "id": 2,
        "slug": "map",
        "canonical_name": "Fosfato Monoamônico (MAP)",
        "category_name": "Fertilizantes Fosfatados",
        "chemical_formula": "NH4H2PO4",
        "cas_rn": "7722-76-1",
        "description": "Fertilizante fosfatado concentrado fornecendo Nitrogênio (11%) e Fósforo (52% P2O5).",
        "typical_nutrients": {"N": 11.0, "P2O5": 52.0},
        "synonyms": ["MAP", "Monoammonium Phosphate"],
        "hs_ncm_codes": ["310540", "31054000"],
    },
    {
        "id": 3,
        "slug": "dap",
        "canonical_name": "Fosfato Diamônico (DAP)",
        "category_name": "Fertilizantes Fosfatados",
        "chemical_formula": "(NH4)2HPO4",
        "cas_rn": "7783-28-0",
        "description": "Fertilizante fosfatado de alta solubilidade contendo 18% N e 46% P2O5.",
        "typical_nutrients": {"N": 18.0, "P2O5": 46.0},
        "synonyms": ["DAP", "Diammonium Phosphate"],
        "hs_ncm_codes": ["310530", "31053000"],
    },
    {
        "id": 4,
        "slug": "cloreto-de-potassio",
        "canonical_name": "Cloreto de Potássio (KCl / MOP)",
        "category_name": "Fertilizantes Potássicos",
        "chemical_formula": "KCl",
        "cas_rn": "7447-40-7",
        "description": "Fonte potássica predominante mundialmente, garantindo 60% de K2O solúvel em água.",
        "typical_nutrients": {"K2O": 60.0},
        "synonyms": ["KCl", "MOP", "Muriate of Potash"],
        "hs_ncm_codes": ["310420", "31042090"],
    },
    {
        "id": 5,
        "slug": "amonia-anidra",
        "canonical_name": "Amônia Anidra",
        "category_name": "Fertilizantes Nitrogenados",
        "chemical_formula": "NH3",
        "cas_rn": "7664-41-7",
        "description": "Matéria-prima básica fundamental para quase todos os fertilizantes nitrogenados (82% N).",
        "typical_nutrients": {"N": 82.0},
        "synonyms": ["Anhydrous Ammonia"],
        "hs_ncm_codes": ["281410"],
    },
    {
        "id": 6,
        "slug": "nitrato-de-amonio",
        "canonical_name": "Nitrato de Amônio",
        "category_name": "Fertilizantes Nitrogenados",
        "chemical_formula": "NH4NO3",
        "cas_rn": "6484-52-2",
        "description": "Fertilizante nitrogenado com ação rápida e residual (33% a 34% N).",
        "typical_nutrients": {"N": 34.0},
        "synonyms": ["Ammonium Nitrate"],
        "hs_ncm_codes": ["310230"],
    },
    {
        "id": 7,
        "slug": "sulfato-de-amonio",
        "canonical_name": "Sulfato de Amônio",
        "category_name": "Fertilizantes Nitrogenados",
        "chemical_formula": "(NH4)2SO4",
        "cas_rn": "7783-20-2",
        "description": "Fonte sólida combinada de Nitrogênio (21% N) e Enxofre (24% S).",
        "typical_nutrients": {"N": 21.0, "S": 24.0},
        "synonyms": ["Ammonium Sulphate"],
        "hs_ncm_codes": ["310221"],
    },
]

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
        """Obtém o cliente Supabase de forma segura, retornando None se falhar."""
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
        return pd.DataFrame(MOCK_GLOBAL_PRODUCTION)

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
        """Obtém indicadores de consumo aparente e taxa de dependência externa do Brasil."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("v_brazil_external_dependency").select("*").execute()
                if res.data:
                    df = pd.DataFrame(res.data)
                    for col in ["national_production_mt", "total_imports_mt", "total_exports_mt", "apparent_consumption_mt", "external_dependency_pct", "ref_year"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    return df
            except Exception as exc:
                logger.warning("Falha ao buscar v_brazil_external_dependency: %s", exc)
        return pd.DataFrame(MOCK_BRAZIL_DEPENDENCY)

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
                        return counts
            except Exception as exc:
                logger.warning("Falha ao buscar brazil_trade_details: %s", exc)
        return pd.DataFrame(MOCK_BRAZIL_UF_DATA)

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_audit_runs(cls) -> pd.DataFrame:
        """Obtém histórico recente de execuções de coleta e integridade das fontes."""
        client = cls._get_client()
        if client:
            try:
                res = client.table("data_collection_runs").select("*, data_sources(name, code)").order("started_at", desc=True).limit(20).execute()
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
                        runs.append({
                            "source_name": src_dict.get("name", "Fonte"),
                            "source_code": src_dict.get("code", "N/A"),
                            "status": r.get("status", "COMPLETED"),
                            "records_count": r.get("records_inserted", 0) or 0,
                            "started_at": r.get("started_at", ""),
                            "execution_time_sec": r.get("execution_time_seconds", 0.0) or 0.0,
                        })
                    return pd.DataFrame(runs)
            except Exception as exc:
                logger.warning("Falha ao buscar data_collection_runs: %s", exc)
        return pd.DataFrame(MOCK_AUDIT_RUNS)

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_seasonality_patterns(cls, fertilizer_name: str = "Todos") -> pd.DataFrame:
        """Obtém curvas e índices de sazonalidade mensal utilizando o caso de uso (RF10)."""
        from app.application.use_cases.calculate_seasonality import CalculateSeasonalityUseCase
        use_case = CalculateSeasonalityUseCase()
        patterns = use_case.execute(fertilizer_name=fertilizer_name)
        return pd.DataFrame([
            {
                "month": p.month,
                "month_name": p.month_name,
                "average_volume_mt": p.average_volume_mt,
                "seasonality_index": p.seasonality_index,
                "peak_status": p.peak_status,
                "crop_calendar_phase": p.crop_calendar_phase,
            }
            for p in patterns
        ])

    @classmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def get_market_insights(cls) -> list[dict[str, Any]]:
        """Gera e retorna os alertas e insights analíticos de inteligência de mercado (RF23)."""
        from app.application.use_cases.generate_insights import GenerateMarketInsightsUseCase
        use_case = GenerateMarketInsightsUseCase()
        insights = use_case.execute()
        return [
            {
                "id": i.id,
                "title": i.title,
                "category": i.category,
                "severity": i.severity,
                "message": i.message,
                "metric_name": i.metric_name,
                "metric_value": i.metric_value,
                "baseline_value": i.baseline_value,
                "recommended_action": i.recommended_action,
                "is_critical": i.is_critical,
            }
            for i in insights
        ]

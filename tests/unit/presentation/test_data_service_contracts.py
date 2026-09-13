"""Testes unitários de alta rigidez para contratos e esquemas dos DataFrames do FertiDataService."""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.presentation.streamlit.services.data_service import FertiDataService


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """Garante que o cache do st.cache_data seja resetado entre os testes."""
    try:
        FertiDataService.get_fertilizer_profiles.clear()
        FertiDataService.get_global_production_rankings.clear()
        FertiDataService.get_bilateral_trade_flows.clear()
        FertiDataService.get_brazil_external_dependency.clear()
        FertiDataService.get_price_benchmark_trends.clear()
        FertiDataService.get_brazil_uf_distribution.clear()
        FertiDataService.get_audit_runs.clear()
    except Exception:
        pass


class TestFertiDataServiceContracts:
    """Validações estritas de esquema, tipos e integridade para todos os métodos de dados."""

    def test_get_fertilizer_profiles_schema(self):
        df = FertiDataService.get_fertilizer_profiles()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) >= 12, "Perfis devem conter no mínimo os 12 fertilizantes homologados."

        required_cols = [
            "id",
            "slug",
            "canonical_name",
            "category_name",
            "chemical_formula",
            "cas_rn",
            "hs_ncm_codes",
            "typical_nutrients",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em fertilizer_profiles"
            assert df[col].notna().all(), f"Coluna '{col}' possui valores nulos inválidos"

    def test_get_global_production_rankings_schema(self):
        df = FertiDataService.get_global_production_rankings()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        required_cols = [
            "fertilizer_name",
            "country_name",
            "country_iso3",
            "standard_quantity_mt",
            "global_market_share_pct",
            "rank_position",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em global_production"

        # Validar consistência de valores
        assert (df["standard_quantity_mt"] >= 0).all()
        assert (df["global_market_share_pct"] >= 0.0).all()
        assert (df["global_market_share_pct"] <= 100.0).all()
        assert (df["rank_position"] >= 1).all()

    def test_get_bilateral_trade_flows_schema(self):
        df = FertiDataService.get_bilateral_trade_flows()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        required_cols = [
            "fertilizer_name",
            "exporter_country",
            "importer_country",
            "total_quantity_mt",
            "total_value_usd",
            "avg_usd_per_mt",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em bilateral_trade_flows"

        # Volumes e valores não podem ser negativos
        assert (df["total_quantity_mt"].dropna() >= 0).all()
        assert (df["total_value_usd"].dropna() >= 0).all()
        assert (df["avg_usd_per_mt"].dropna() >= 0).all()

    def test_get_brazil_external_dependency_schema(self):
        df = FertiDataService.get_brazil_external_dependency()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        required_cols = [
            "fertilizer_name",
            "ref_year",
            "national_production_mt",
            "total_imports_mt",
            "total_exports_mt",
            "apparent_consumption_mt",
            "external_dependency_pct",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em brazil_external_dependency"

        valid_deps = df["external_dependency_pct"].dropna()
        assert (valid_deps >= 0.0).all()
        # Em anos parciais ou com forte desova/reexportação de estoques (ex: 2026), import/consumo pode ultrapassar 100%
        assert (valid_deps <= 200.0).all()

    def test_get_price_benchmark_trends_schema(self):
        df = FertiDataService.get_price_benchmark_trends()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        required_cols = [
            "fertilizer_id",
            "fertilizer_name",
            "nutrient_type",
            "benchmark_name",
            "price_date",
            "standard_price_usd_per_mt",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em price_benchmark_trends"

        # Preços devem ser estritamente positivos
        assert (df["standard_price_usd_per_mt"] > 0).all()

    def test_get_brazil_uf_distribution_schema(self):
        df = FertiDataService.get_brazil_uf_distribution()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) >= 8, "A distribuição de estados deve conter no mínimo os 8 maiores polos agrícolas"

        required_cols = ["uf", "state_name", "share_pct", "quantity_mt"]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em brazil_uf_distribution"

        # A soma das participações deve fechar em 100%
        assert 99.0 <= df["share_pct"].sum() <= 101.0

    def test_get_audit_runs_schema(self):
        df = FertiDataService.get_audit_runs()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        required_cols = ["source_name", "source_code", "status", "records_count"]
        for col in required_cols:
            assert col in df.columns, f"Coluna obrigatória '{col}' ausente em audit_runs"

    def test_get_global_map_data_all_flow_types(self):
        for flow in ["Produção", "Exportação", "Importação"]:
            df_map = FertiDataService.get_global_map_data(fertilizer_name="Ureia", year=2023, flow_type=flow)
            assert isinstance(df_map, pd.DataFrame)
            assert not df_map.empty, f"Mapa global vazio para o fluxo: {flow}"
            assert "country_iso3" in df_map.columns
            assert "standard_quantity_mt" in df_map.columns

    def test_get_fertilizer_by_slug_or_id_strict(self):
        # Slug existente
        f1 = FertiDataService.get_fertilizer_by_slug_or_id("ureia")
        assert f1 is not None
        assert f1["id"] == 1
        assert f1["canonical_name"] == "Ureia"

        # ID numérico existente
        f2 = FertiDataService.get_fertilizer_by_slug_or_id(2)
        assert f2 is not None
        assert f2["slug"] == "map"

        # Slug inexistente
        assert FertiDataService.get_fertilizer_by_slug_or_id("inexistente_xyz") is None
        # ID inexistente
        assert FertiDataService.get_fertilizer_by_slug_or_id(9999) is None

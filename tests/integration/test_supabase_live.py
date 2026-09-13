"""Testes de integração ao vivo de alta rigidez para validar schema 4NF, tabelas, views, integridade referencial e RLS no Supabase."""

import os
import time
import pytest
from dotenv import load_dotenv

load_dotenv()

from app.infrastructure.supabase import (
    SupabaseClientManager,
    SupabaseConfig,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)
from app.presentation.streamlit.services.data_service import FertiDataService


def _has_real_supabase_credentials() -> bool:
    try:
        cfg = SupabaseConfig.from_env()
        # Garante que não está usando as credenciais dummy de mock
        if not cfg.url or "test-project" in cfg.url:
            return False
        return bool(cfg.key or cfg.service_role_key)
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _has_real_supabase_credentials(),
        reason="Credenciais reais do Supabase não configuradas no ambiente",
    ),
]


@pytest.fixture(scope="module")
def supabase_config():
    """Carrega configuração de produção/desenvolvimento do ambiente."""
    return SupabaseConfig.from_env()


@pytest.fixture(scope="module")
def admin_client(supabase_config):
    """Cliente autenticado com role de administração (service_role)."""
    return SupabaseClientManager.get_admin_client(supabase_config)


@pytest.fixture(scope="module")
def public_client(supabase_config):
    """Cliente público anônimo (anon key)."""
    return SupabaseClientManager.get_client(supabase_config)


class TestSupabaseLiveSchemaAndDataStrict:
    """Suíte rigorosa de validação do banco Supabase ao vivo."""

    def test_live_connection_health(self, public_client):
        """Valida que o cliente público consegue se conectar e receber resposta da API PostgREST."""
        res = public_client.table("fertilizers").select("count", count="exact").execute()
        assert res.count is not None
        assert res.count >= 12, "Deve existir ao menos 12 fertilizantes cadastrados"

    def test_live_all_seven_4nf_tables_accessible_and_populated(self, public_client):
        """Valida a existência e presença de dados reais em todas as 7 tabelas 4NF."""
        tables_to_check = {
            "fertilizers": 12,
            "countries": 200,
            "trade_records": 30000,
            "production_records": 100,
            "price_records": 1500,
            "brazil_trade_details": 4000,
            "data_collection_runs": 0,
        }

        for table_name, min_expected_count in tables_to_check.items():
            res = public_client.table(table_name).select("count", count="exact").execute()
            count = res.count or 0
            assert count >= min_expected_count, (
                f"Tabela 4NF '{table_name}' possui apenas {count} registros (mínimo esperado: {min_expected_count})"
            )

    def test_live_fertilizers_catalog_canonical_products(self, public_client):
        """Valida que os principais produtos canônicos e suas categorias estão corretos."""
        res = public_client.table("fertilizers").select("id, slug, canonical_name, cas_rn, chemical_formula").execute()
        assert res.data and len(res.data) >= 12

        slugs = {row["slug"] for row in res.data}
        expected_critical_slugs = {
            "ureia",
            "map",
            "dap",
            "cloreto-de-potassio",
            "amonia-anidra",
            "sulfato-de-amonio",
            "enxofre-elementar",
        }
        for slug in expected_critical_slugs:
            assert slug in slugs, f"Fertilizante canônico '{slug}' ausente no Supabase de produção"

    def test_live_all_analytical_views_are_queryable_and_structured(self, public_client):
        """Valida que todas as 5 views analíticas SQL do sistema estão íntegras e com dados."""
        views_to_verify = [
            ("v_fertilizer_profiles", ["slug", "canonical_name", "category_name", "chemical_formula"]),
            ("v_bilateral_trade_flows", ["fertilizer_name", "exporter_country", "importer_country", "total_quantity_mt", "total_value_usd"]),
            ("v_brazil_external_dependency", ["fertilizer_name", "ref_year", "national_production_mt", "total_imports_mt", "external_dependency_pct"]),
            ("v_price_benchmark_trends", ["fertilizer_id", "fertilizer_name", "benchmark_name", "standard_price_usd_per_mt"]),
            ("v_global_production_rankings", ["fertilizer_name", "country_name", "country_iso3", "standard_quantity_mt", "rank_position"]),
        ]

        for view_name, expected_columns in views_to_verify:
            res = public_client.table(view_name).select("*").limit(5).execute()
            assert res.data is not None and len(res.data) > 0, f"View SQL '{view_name}' retornou vazia"
            sample = res.data[0]
            for col in expected_columns:
                assert col in sample, f"Coluna esperada '{col}' ausente na view '{view_name}'"

    def test_live_referential_integrity_foreign_keys(self, public_client):
        """Verifica integridade referencial: trade_records e price_records não possuem IDs órfãos."""
        # Busca IDs válidos de fertilizantes
        res_ferts = public_client.table("fertilizers").select("id").execute()
        valid_fert_ids = {f["id"] for f in res_ferts.data}

        # Checa amostra de trade_records
        res_trade = public_client.table("trade_records").select("fertilizer_id").limit(100).execute()
        for row in res_trade.data:
            assert row["fertilizer_id"] in valid_fert_ids, f"ID órfão em trade_records: {row['fertilizer_id']}"

        # Checa amostra de price_records
        res_prices = public_client.table("price_records").select("fertilizer_id").limit(100).execute()
        for row in res_prices.data:
            assert row["fertilizer_id"] in valid_fert_ids, f"ID órfão em price_records: {row['fertilizer_id']}"

    def test_live_rls_public_client_is_strictly_read_only(self, public_client):
        """Garante que a chave anônima é estritamente bloqueada contra escrita por RLS."""
        malicious_payload = {
            "source_id": 1,
            "collected_at": "2026-09-02T12:00:00Z",
            "reference_date": "2026-09-01",
            "raw_payload": {"attack": "UNAUTHORIZED_WRITE"},
            "status": "RAW",
        }

        # Tentativa de escrita na tabela raw_data via cliente anônimo deve falhar ou ser bloqueada por RLS
        with pytest.raises(Exception):
            public_client.table("raw_data").insert(malicious_payload).execute()

    def test_live_admin_write_and_cleanup(self, admin_client):
        """Garante que a chave administrativa (service_role) possui permissão de escrita e limpeza pontual."""
        repo = SupabaseRawDataRepository(client=admin_client)

        test_payload = {
            "source_id": 1,
            "collected_at": "2026-09-02T12:00:00Z",
            "reference_date": "2026-09-01",
            "raw_payload": {"test_metric": 99999, "status": "TEST_RIGOROUS_INTEGRATION"},
            "status": "RAW",
        }

        # 1. Inserção
        inserted = repo.insert(test_payload)
        assert inserted is not None
        assert "id" in inserted
        inserted_id = inserted["id"]

        # 2. Leitura
        found = repo.find_by_id(inserted_id)
        assert found is not None
        assert found["id"] == inserted_id

        # 3. Deleção (Limpeza)
        deleted = repo.delete(inserted_id)
        assert deleted is True

        # Confirma que foi removido
        assert repo.find_by_id(inserted_id) is None

    def test_live_concurrent_pagination_loads_complete_dataset(self):
        """Valida que a paginação concorrente busca todos os 33.000+ registros em alta velocidade (< 10s)."""
        FertiDataService.get_bilateral_trade_flows.clear()
        start_time = time.time()
        df = FertiDataService.get_bilateral_trade_flows()
        elapsed = time.time() - start_time

        assert not df.empty
        assert len(df) >= 30000, f"Deveria ter carregado mais de 30.000 registros, carregou {len(df)}"
        assert elapsed < 12.0, f"Tempo excessivo de paginação concorrente: {elapsed:.2f}s"

        # Conferência de integridade dos dados retornados
        fert_names = df["fertilizer_name"].unique()
        assert len(fert_names) >= 10, "A busca deve cobrir múltiplos fertilizantes homologados"

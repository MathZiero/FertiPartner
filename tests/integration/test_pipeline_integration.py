"""Testes de integração ponta a ponta para a esteira de ingestão e pipelines do FertiPartner."""

import os
from datetime import datetime, timezone
import pytest
from dotenv import load_dotenv

load_dotenv()

from app.infrastructure.supabase import (
    SupabaseClientManager,
    SupabaseConfig,
    SupabaseRawDataRepository,
)
from app.infrastructure.collectors.base import BaseCollector


def _has_real_supabase_credentials() -> bool:
    try:
        cfg = SupabaseConfig.from_env()
        if not cfg.url or "test-project" in cfg.url:
            return False
        return bool(cfg.service_role_key)
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _has_real_supabase_credentials(),
        reason="Credenciais administrativas do Supabase não configuradas no ambiente",
    ),
]


class MockDataPipelineCollector(BaseCollector):
    """Coletor simulado para teste de ciclo de vida completo do pipeline."""

    def run(self, **kwargs):
        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"test_run": True, "purpose": "INTEGRATION_TEST"},
        )
        # 1. Salvar payload bruto em raw_data
        raw_id = self.store_raw_payload(
            endpoint_url="https://integration.test/pipeline",
            payload_data={"price_sample": 550.0, "status": "STAGING"},
            collection_run_id=run_id,
            reference_date="2026-09-01",
        )

        # 2. Inserir dado 4NF na tabela price_records (com data futura de teste)
        fert_id = self.resolve_fertilizer_id("ureia") or 1
        price_row = {
            "fertilizer_id": fert_id,
            "benchmark_id": 1,
            "price_date": "2099-12-31",  # Data futura para isolamento estrito
            "frequency": "MONTHLY",
            "price_type": "BENCHMARK",
            "original_price": 550.0,
            "currency_code": "USD",
            "original_unit_code": "MT",
            "standard_price_usd_per_mt": 550.0,
            "data_status": "OFFICIAL",
            "source_id": self.source_id,
            "raw_data_id": raw_id,
        }

        upsert_res = (
            self.supabase.table("price_records")
            .upsert(
                [price_row],
                on_conflict="fertilizer_id, benchmark_id, price_date, price_type, source_id",
            )
            .execute()
        )

        self.finish_collection_run(
            run_id=run_id,
            records_fetched=1,
            records_inserted=1,
            status="SUCCESS",
        )

        return {
            "run_id": run_id,
            "raw_id": raw_id,
            "inserted": upsert_res.data,
        }


class TestPipelineIntegration:
    """Valida o fluxo completo de ingestão: Coletor -> raw_data -> 4NF -> Consulta -> Limpeza."""

    def test_full_pipeline_ingestion_and_cleanup(self):
        cfg = SupabaseConfig.from_env()
        admin_client = SupabaseClientManager.get_admin_client(cfg)

        collector = MockDataPipelineCollector(supabase_client=admin_client, source_id=1)
        result = collector.run()

        run_id = result["run_id"]
        raw_id = result["raw_id"]

        try:
            # 1. Verificar que raw_data foi registrado
            raw_repo = SupabaseRawDataRepository(client=admin_client)
            raw_record = raw_repo.find_by_id(raw_id)
            assert raw_record is not None
            assert raw_record["id"] == raw_id

            # 2. Verificar que o registro 4NF foi persistido
            res_price = (
                admin_client.table("price_records")
                .select("*")
                .eq("price_date", "2099-12-31")
                .eq("price_type", "BENCHMARK")
                .execute()
            )
            assert len(res_price.data) == 1
            assert res_price.data[0]["standard_price_usd_per_mt"] == 550.0

            # 3. Verificar auditoria em data_collection_runs
            res_run = admin_client.table("data_collection_runs").select("*").eq("id", run_id).execute()
            assert len(res_run.data) == 1
            assert res_run.data[0]["status"] == "SUCCESS"
            assert res_run.data[0]["records_inserted"] == 1

        finally:
            # Limpeza cirúrgica dos dados de teste
            admin_client.table("price_records").delete().eq("price_date", "2099-12-31").eq("price_type", "BENCHMARK").execute()
            raw_repo.delete(raw_id)
            admin_client.table("data_collection_runs").delete().eq("id", run_id).execute()

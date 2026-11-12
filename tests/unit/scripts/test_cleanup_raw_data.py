"""Testes unitários para o utilitário de governança e compactação scripts/cleanup_raw_data.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.cleanup_raw_data import compact_domain_payload, run_cleanup


def test_compact_domain_payload_comtrade_strips_nulls_and_world_partner():
    raw_comtrade = {
        "elapsedTime": "3.15 secs",
        "count": 2,
        "data": [
            {
                "period": "2023",
                "reporterCode": 76,
                "partnerCode": 0,  # Agregado mundial (não bilateral) -> deve ser filtrado
                "cmdCode": "310210",
                "flowCode": "M",
                "netWgt": 5000.0,
                "primaryValue": 1000.0,
            },
            {
                "period": "2023",
                "reporterCode": 76,
                "partnerCode": 643,
                "cmdCode": "310210",
                "flowCode": "M",
                "netWgt": 2500.0,
                "primaryValue": 500.0,
                "cmdDesc": None,
                "motDesc": "Sea",
                "legacyEstimationFlag": 0,
            },
        ],
    }

    compacted = compact_domain_payload(3, raw_comtrade)
    assert "elapsedTime" not in compacted
    assert compacted["count"] == 1
    assert len(compacted["data"]) == 1
    item = compacted["data"][0]
    assert item["partnerCode"] == 643
    assert item["netWgt"] == 2500.0
    assert "cmdDesc" not in item
    assert "motDesc" not in item
    assert "legacyEstimationFlag" not in item


def test_compact_domain_payload_faostat_keeps_only_fertilizer_items():
    raw_faostat = {
        "metadata": {"datasource": "FAOSTAT", "processing_time": 0.87, "dsd": [{"col": "X"}]},
        "data": [
            {"Area Code": "21", "Item Code": "515", "Item": "Apples", "Value": "400.0"},
            {"Area Code": "21", "Item Code": "4001", "Item": "Urea", "Value": "550.0"},
        ],
    }

    compacted = compact_domain_payload(9, raw_faostat)
    assert len(compacted["data"]) == 1
    assert compacted["data"][0]["Item Code"] == "4001"
    assert "processing_time" not in compacted.get("metadata", {})
    assert "dsd" not in compacted.get("metadata", {})


def test_run_cleanup_identifies_and_deletes_orphans_and_consolidates_duplicates():
    mock_client = MagicMock()

    # trade_records referencia os IDs 10 e 20 (que são duplicatas do mesmo endpoint)
    # ID 30 não é referenciado por nenhuma tabela (órfão)
    def table_side_effect(name: str):
        tbl = MagicMock()
        if name == "trade_records":
            tbl.select.return_value.not_.is_.return_value.range.return_value.execute.return_value.data = [
                {"raw_data_id": 10},
                {"raw_data_id": 20},
            ]
        elif name in ("production_records", "price_records", "consumption_records", "country_indicators"):
            tbl.select.return_value.not_.is_.return_value.range.return_value.execute.return_value.data = []
        elif name == "raw_data":
            tbl.select.return_value.order.return_value.range.return_value.execute.return_value.data = [
                {"id": 10, "source_id": 7, "endpoint_url": "https://api.fred/s1", "payload_hash": "h1"},
                {"id": 20, "source_id": 7, "endpoint_url": "https://api.fred/s1", "payload_hash": "h2"},
                {"id": 30, "source_id": 9, "endpoint_url": "https://api.fao/pp1", "payload_hash": "h3"},
            ]
            tbl.select.return_value.in_.return_value.execute.return_value.data = [
                {
                    "id": 20,
                    "source_id": 7,
                    "payload_hash": "old_hash",
                    "raw_payload": {"realtime_start": "2026-11-11", "observations": [{"date": "2026-01-01", "value": "10"}]},
                }
            ]
        return tbl

    mock_client.table.side_effect = table_side_effect

    summary = run_cleanup(client=mock_client, dry_run=False, compact_payloads=True)

    assert summary["total_before"] == 3
    assert summary["repointed_fks"] == 1  # ID 10 consolidado no ID 20
    assert summary["referenced_kept"] == 1  # Apenas ID 20 mantido
    assert summary["orphans_found"] == 2  # ID 10 (após consolidação) + ID 30
    assert summary["orphans_deleted"] == 2
    assert summary["payloads_compacted"] == 1


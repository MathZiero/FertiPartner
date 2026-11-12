"""Utilitário de governança, deduplicação por endpoint, remoção de órfãos e compactação de public.raw_data.

Garante que a tabela `public.raw_data` permaneça enxuta e dentro dos limites do plano Free do Supabase:
  1. Identifica todos os `raw_data_id` efetivamente referenciados pelas 5 tabelas de fatos 4NF.
  2. Consolida duplicatas de `(source_id, endpoint_url)`, redirecionando chaves estrangeiras para o ID canônico.
  3. Remove em lotes seguros todos os registros órfãos de `public.raw_data` (ex: coletas sem itens de fertilizantes).
  4. Compacta os payloads JSONB ativos removendo metadados voláteis (`processing_time`, `elapsedTime`,
     `realtime_start`, `realtime_end`, `dsd`), colunas nulas e itens não pertencentes ao catálogo de fertilizantes.

Usage:
    uv run python scripts/cleanup_raw_data.py --dry-run
    uv run python scripts/cleanup_raw_data.py --compact-payloads
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.collectors.faostat_collector import FAO_ITEM_FERTILIZER_MAP
from app.infrastructure.collectors.faostat_prices_collector import FAO_PRICE_ITEM_FERTILIZER_MAP
from app.infrastructure.supabase.client import get_supabase_admin_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cleanup_raw_data")

FACT_TABLES: tuple[str, ...] = (
    "trade_records",
    "production_records",
    "price_records",
    "consumption_records",
    "country_indicators",
)

COMTRADE_ESSENTIAL_KEYS: tuple[str, ...] = (
    "period",
    "reporterCode",
    "partnerCode",
    "cmdCode",
    "flowCode",
    "netWgt",
    "qty",
    "primaryValue",
    "cifvalue",
    "fobvalue",
)


def compact_domain_payload(source_id: int, raw_payload: Any) -> dict[str, Any]:
    """Aplica compactação específica por domínio preservando todos os dados auditáveis de fertilizantes."""
    sanitized = BaseCollector.sanitize_raw_payload(raw_payload)
    data_list = sanitized.get("data")

    # UN Comtrade (source_id=3): mantém apenas registros bilaterais e colunas essenciais
    if source_id == 3 and isinstance(data_list, list):
        compact_items: list[dict[str, Any]] = []
        for item in data_list:
            if not isinstance(item, dict):
                continue
            p_code = item.get("partnerCode")
            if p_code is not None and int(p_code) == 0:
                continue
            compact_item = {
                k: item[k]
                for k in COMTRADE_ESSENTIAL_KEYS
                if k in item and item[k] is not None and item[k] != ""
            }
            if compact_item:
                compact_items.append(compact_item)
        return {"data": compact_items, "count": len(compact_items)}

    # FAOSTAT RFB (source_id=2) e PP (source_id=9): mantém apenas códigos de fertilizantes
    if source_id in (2, 9) and isinstance(data_list, list):
        allowed_codes = set(FAO_ITEM_FERTILIZER_MAP.keys()) | set(FAO_PRICE_ITEM_FERTILIZER_MAP.keys())
        filtered_items = [
            item
            for item in data_list
            if isinstance(item, dict) and str(item.get("Item Code", "")).strip() in allowed_codes
        ]
        result: dict[str, Any] = {"data": filtered_items}
        if "metadata" in sanitized and isinstance(sanitized["metadata"], dict):
            result["metadata"] = sanitized["metadata"]
        return result

    return sanitized


def fetch_referenced_raw_ids(client: Any) -> set[int]:
    """Retorna o conjunto de todos os `raw_data_id` referenciados pelas tabelas de fatos."""
    referenced: set[int] = set()
    for tbl in FACT_TABLES:
        offset = 0
        while True:
            res = (
                client.table(tbl)
                .select("raw_data_id")
                .not_.is_("raw_data_id", "null")
                .range(offset, offset + 999)
                .execute()
            )
            rows = res.data or []
            for r in rows:
                if isinstance(r, dict) and r.get("raw_data_id") is not None:
                    referenced.add(int(r["raw_data_id"]))
            if len(rows) < 1000:
                break
            offset += 1000
    return referenced


def fetch_all_raw_metadata(client: Any) -> list[dict[str, Any]]:
    """Lista metadados leves (id, source_id, endpoint_url, payload_hash) de toda a tabela raw_data."""
    all_rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        res = (
            client.table("raw_data")
            .select("id, source_id, endpoint_url, payload_hash")
            .order("id", desc=False)
            .range(offset, offset + 999)
            .execute()
        )
        rows = [r for r in (res.data or []) if isinstance(r, dict)]
        all_rows.extend(rows)
        if len(rows) < 1000:
            break
        offset += 1000
    return all_rows


def run_cleanup(
    client: Any | None = None,
    dry_run: bool = False,
    compact_payloads: bool = True,
    batch_size: int = 25,
) -> dict[str, int]:
    """Executa deduplicação por endpoint, limpeza de órfãos e compactação de payloads em raw_data."""
    supabase = client or get_supabase_admin_client()

    logger.info("Consultando referências ativas nas tabelas de fatos 4NF...")
    referenced_ids = fetch_referenced_raw_ids(supabase)
    logger.info("Total de raw_data_id referenciados: %d", len(referenced_ids))

    logger.info("Carregando metadados de public.raw_data...")
    all_raw = fetch_all_raw_metadata(supabase)
    total_before = len(all_raw)
    logger.info("Total de registros em public.raw_data antes da limpeza: %d", total_before)

    # 1. Agrupar por (source_id, endpoint_url) para consolidar duplicatas referenciadas
    by_endpoint: dict[tuple[int, str], list[int]] = {}
    for row in all_raw:
        rid = int(row["id"])
        sid = int(row["source_id"])
        ep = str(row.get("endpoint_url") or "")
        by_endpoint.setdefault((sid, ep), []).append(rid)

    repointed_fks = 0
    for (sid, ep), ids in by_endpoint.items():
        if len(ids) <= 1:
            continue
        # Escolhe como canônico o maior ID referenciado, ou o maior ID geral
        ref_in_group = [i for i in ids if i in referenced_ids]
        canonical_id = max(ref_in_group) if ref_in_group else max(ids)
        duplicate_ref_ids = [i for i in ref_in_group if i != canonical_id]

        if duplicate_ref_ids:
            repointed_fks += len(duplicate_ref_ids)
            if not dry_run:
                for tbl in FACT_TABLES:
                    supabase.table(tbl).update({"raw_data_id": canonical_id}).in_("raw_data_id", duplicate_ref_ids).execute()
            for dup_id in duplicate_ref_ids:
                referenced_ids.discard(dup_id)
            referenced_ids.add(canonical_id)

    # 2. Identificar todos os registros órfãos (não referenciados após consolidação)
    orphan_ids = [int(r["id"]) for r in all_raw if int(r["id"]) not in referenced_ids]
    logger.info(
        "Órfãos identificados para remoção: %d (de %d registros totais)",
        len(orphan_ids),
        total_before,
    )

    deleted_count = 0
    if orphan_ids and not dry_run:
        for i in range(0, len(orphan_ids), batch_size):
            chunk = orphan_ids[i : i + batch_size]
            try:
                supabase.table("raw_data").delete().in_("id", chunk).execute()
                deleted_count += len(chunk)
            except Exception as exc:
                logger.warning("Falha no lote de %d IDs (%s). Tentando individualmente...", len(chunk), exc)
                for single_id in chunk:
                    try:
                        supabase.table("raw_data").delete().eq("id", single_id).execute()
                        deleted_count += 1
                    except Exception as single_exc:
                        logger.error("Erro ao deletar raw_data id=%d: %s", single_id, single_exc)
            if deleted_count % 500 == 0 or deleted_count >= len(orphan_ids):
                logger.info("  Removidos %d/%d registros órfãos...", deleted_count, len(orphan_ids))

    # 3. Compactar payloads ativos referenciados
    compacted_count = 0
    bytes_saved = 0
    if compact_payloads:
        remaining_ids = sorted(referenced_ids)
        logger.info("Verificando compactação de %d payloads ativos...", len(remaining_ids))
        chunk_sz = 50
        for i in range(0, len(remaining_ids), chunk_sz):
            id_chunk = remaining_ids[i : i + chunk_sz]
            res = (
                supabase.table("raw_data")
                .select("id, source_id, payload_hash, raw_payload")
                .in_("id", id_chunk)
                .execute()
            )
            for row in res.data or []:
                if not isinstance(row, dict):
                    continue
                row_id = row.get("id")
                source_id = row.get("source_id")
                if not isinstance(row_id, (int, str)) or not isinstance(source_id, (int, str)):
                    continue
                rid = int(row_id)
                sid = int(source_id)
                old_payload = row.get("raw_payload")
                old_json = json.dumps(old_payload, sort_keys=True, default=str)

                new_payload = compact_domain_payload(sid, old_payload)
                new_json = json.dumps(new_payload, sort_keys=True, default=str)
                new_hash = hashlib.sha256(new_json.encode("utf-8")).hexdigest()

                if len(new_json) < len(old_json) or new_hash != row.get("payload_hash"):
                    diff = max(0, len(old_json) - len(new_json))
                    bytes_saved += diff
                    compacted_count += 1
                    if not dry_run:
                        supabase.table("raw_data").update(
                            {"raw_payload": new_payload, "payload_hash": new_hash}
                        ).eq("id", rid).execute()

            if (i + chunk_sz) % 500 == 0 or (i + chunk_sz) >= len(remaining_ids):
                logger.info(
                    "  Processados %d/%d registros ativos (compactados=%d, economia=%.2f MB)...",
                    min(i + chunk_sz, len(remaining_ids)),
                    len(remaining_ids),
                    compacted_count,
                    bytes_saved / (1024 * 1024),
                )

    return {
        "total_before": total_before,
        "referenced_kept": len(referenced_ids),
        "orphans_found": len(orphan_ids),
        "orphans_deleted": deleted_count,
        "repointed_fks": repointed_fks,
        "payloads_compacted": compacted_count,
        "bytes_saved": bytes_saved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpeza e compactação permanente de public.raw_data")
    parser.add_argument("--dry-run", action="store_true", help="Simula a operação sem alterar o banco")
    parser.add_argument(
        "--compact-payloads",
        action="store_true",
        default=True,
        help="Compacta payloads JSONB ativos removendo metadados voláteis e campos nulos (padrão: True)",
    )
    args = parser.parse_args()

    summary = run_cleanup(dry_run=args.dry_run, compact_payloads=args.compact_payloads)
    print("\n" + "=" * 70)
    print("RESUMO DE OTIMIZAÇÃO DE PUBLIC.RAW_DATA")
    print("=" * 70)
    print(f"Registros antes da limpeza : {summary['total_before']:,}")
    print(f"Registros ativos mantidos  : {summary['referenced_kept']:,}")
    print(f"FKs consolidadas           : {summary['repointed_fks']:,}")
    print(f"Órfãos identificados       : {summary['orphans_found']:,}")
    print(f"Órfãos removidos           : {summary['orphans_deleted']:,}")
    print(f"Payloads compactados       : {summary['payloads_compacted']:,}")
    print(f"Espaço JSONB economizado   : {summary['bytes_saved'] / (1024 * 1024):.2f} MB")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()


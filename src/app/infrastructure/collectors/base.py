"""Classe base para coletores de dados: gerencia auditoria, persistência bruta e hashing."""

from abc import ABC, abstractmethod
import hashlib
import json
import logging
from typing import Any, Mapping, cast
from supabase import Client
from app.infrastructure.http import ResilientHttpClient
from app.infrastructure.supabase import SupabaseClientManager, SupabaseConfig

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data ingestion pipelines."""

    VOLATILE_PAYLOAD_KEYS: frozenset[str] = frozenset({
        "processing_time",
        "elapsedTime",
        "realtime_start",
        "realtime_end",
        "processo_info",
        "dsd",
        "lastupdated",
    })

    def __init__(
        self,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
        source_id: int = 1,
    ) -> None:
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            config = SupabaseConfig.from_env()
            self.supabase = SupabaseClientManager.get_admin_client(config)

        self.http = http_client or ResilientHttpClient()
        self.source_id = source_id

        # In-memory caches for fast foreign-key resolution
        self._countries_by_iso: dict[str, int] = {}
        self._countries_by_name: dict[str, int] = {}
        self._fertilizers_by_slug: dict[str, int] = {}
        self._load_reference_caches()

    def _load_reference_caches(self) -> None:
        """Pre-load countries and fertilizers into memory for zero-latency foreign-key resolution."""
        try:
            countries_res = self.supabase.table("countries").select("id, iso2, iso3, name").execute()
            countries_data = cast(list[dict[str, Any]], countries_res.data)
            if countries_data:
                for c in countries_data:
                    cid = int(c["id"])
                    if c.get("iso2"):
                        self._countries_by_iso[str(c["iso2"]).strip().upper()] = cid
                    if c.get("iso3"):
                        self._countries_by_iso[str(c["iso3"]).strip().upper()] = cid
                    if c.get("name"):
                        self._countries_by_name[str(c["name"]).strip().lower()] = cid

            fert_res = self.supabase.table("fertilizers").select("id, slug").execute()
            fert_data = cast(list[dict[str, Any]], fert_res.data)
            if fert_data:
                for f in fert_data:
                    self._fertilizers_by_slug[str(f["slug"]).strip().lower()] = int(f["id"])
        except Exception as exc:
            logger.warning("Could not pre-load reference caches from Supabase: %s", exc)

    def resolve_country_id(self, code_or_name: str | None) -> int | None:
        """Resolve country ID by ISO2, ISO3, or Portuguese/English name."""
        if not code_or_name:
            return None
        clean = code_or_name.strip()
        upper = clean.upper()
        if upper in self._countries_by_iso:
            return self._countries_by_iso[upper]
        lower = clean.lower()
        if lower in self._countries_by_name:
            return self._countries_by_name[lower]
        return None

    def resolve_fertilizer_id(self, slug: str | None) -> int | None:
        """Resolve fertilizer ID by its canonical slug."""
        if not slug:
            return None
        return self._fertilizers_by_slug.get(slug.strip().lower())

    def start_collection_run(
        self,
        source_id: int | None = None,
        trigger_type: str = "MANUAL",
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Start an audit run in data_collection_runs and return its run UUID."""
        sid = source_id or self.source_id
        payload = {
            "source_id": sid,
            "trigger_type": trigger_type,
            "status": "RUNNING",
            "metadata": dict(metadata or {}),
        }
        res = self.supabase.table("data_collection_runs").insert(payload).execute()
        runs_data = cast(list[dict[str, Any]], res.data)
        if runs_data and len(runs_data) > 0:
            run_id = str(runs_data[0]["id"])
            logger.info("Started collection run %s for source_id=%d", run_id, sid)
            return run_id
        raise RuntimeError("Failed to create record in data_collection_runs")

    def finish_collection_run(
        self,
        run_id: str,
        records_fetched: int,
        records_inserted: int,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> None:
        """Mark a collection run as finished with metrics and status."""
        update_data: dict[str, Any] = {
            "finished_at": "NOW()",
            "status": status,
            "records_fetched": records_fetched,
            "records_inserted": records_inserted,
        }
        if error_message:
            update_data["error_message"] = error_message[:2000]

        self.supabase.table("data_collection_runs").update(update_data).eq("id", run_id).execute()
        logger.info(
            "Finished collection run %s: status=%s, fetched=%d, inserted=%d",
            run_id, status, records_fetched, records_inserted
        )

    @classmethod
    def _clean_payload_node(cls, node: Any) -> Any:
        """Recursively strip volatile metadata keys and null/empty values."""
        if isinstance(node, dict):
            cleaned: dict[str, Any] = {}
            for k, v in node.items():
                if k in cls.VOLATILE_PAYLOAD_KEYS:
                    continue
                if v is None or v == "":
                    continue
                cleaned_v = cls._clean_payload_node(v)
                if cleaned_v is None or cleaned_v == "":
                    continue
                cleaned[k] = cleaned_v
            return cleaned
        if isinstance(node, list):
            return [cls._clean_payload_node(item) for item in node]
        return node

    @classmethod
    def sanitize_raw_payload(cls, payload_data: Any) -> dict[str, Any]:
        """Return a deterministic, compacted JSONB-ready dict stripped of volatile runtime metadata."""
        root = payload_data if isinstance(payload_data, dict) else {"data": payload_data}
        cleaned = cls._clean_payload_node(root)
        return cleaned if isinstance(cleaned, dict) else {"data": cleaned}

    def store_raw_payload(
        self,
        endpoint_url: str,
        payload_data: Any,
        source_id: int | None = None,
        collection_run_id: str | None = None,
        reference_date: str | None = None,
    ) -> int:
        """Store or update compacted raw payload in raw_data with sha256 hash and return row ID."""
        sid = source_id or self.source_id
        sanitized_payload = self.sanitize_raw_payload(payload_data)
        json_str = json.dumps(sanitized_payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        # 1. Deduplicação por hash: reutiliza o registro existente se o mesmo payload já tiver sido arquivado
        try:
            existing = (
                self.supabase.table("raw_data")
                .select("id")
                .eq("payload_hash", payload_hash)
                .limit(1)
                .execute()
            )
            if existing and existing.data and isinstance(existing.data, list) and len(existing.data) > 0:
                first = existing.data[0]
                if isinstance(first, dict) and "id" in first:
                    first_id = first["id"]
                    if isinstance(first_id, (int, str)):
                        existing_id = int(first_id)
                        logger.debug("Raw payload com hash %s já armazenado (id=%d); reutilizando.", payload_hash, existing_id)
                        return existing_id
        except Exception as exc:
            logger.debug("Falha ao verificar existência de hash em raw_data: %s", exc)

        # 2. Upsert por (source_id, endpoint_url): atualiza in-place se o endpoint já existe, evitando órfãos
        try:
            existing_ep = (
                self.supabase.table("raw_data")
                .select("id")
                .eq("source_id", sid)
                .eq("endpoint_url", endpoint_url)
                .order("id", desc=True)
                .limit(1)
                .execute()
            )
            if existing_ep and existing_ep.data and isinstance(existing_ep.data, list) and len(existing_ep.data) > 0:
                first_ep = existing_ep.data[0]
                if isinstance(first_ep, dict) and "id" in first_ep:
                    ep_id_raw = first_ep["id"]
                    if isinstance(ep_id_raw, (int, str)):
                        existing_ep_id = int(ep_id_raw)
                        update_payload: dict[str, Any] = {
                            "collection_run_id": collection_run_id,
                            "payload_hash": payload_hash,
                            "raw_payload": sanitized_payload,
                            "reference_date": reference_date,
                            "status": "PROCESSED",
                            "collected_at": "NOW()",
                        }
                        self.supabase.table("raw_data").update(update_payload).eq("id", existing_ep_id).execute()
                        logger.debug(
                            "Raw payload atualizado in-place para endpoint %s (id=%d).",
                            endpoint_url,
                            existing_ep_id,
                        )
                        return existing_ep_id
        except Exception as exc:
            logger.debug("Falha ao verificar/atualizar endpoint existente em raw_data: %s", exc)

        insert_payload = {
            "source_id": sid,
            "collection_run_id": collection_run_id,
            "endpoint_url": endpoint_url,
            "payload_hash": payload_hash,
            "raw_payload": sanitized_payload,
            "reference_date": reference_date,
            "status": "PROCESSED",
        }

        res = self.supabase.table("raw_data").insert(insert_payload).execute()
        rows_data = cast(list[dict[str, Any]], res.data)
        if rows_data and len(rows_data) > 0:
            return int(rows_data[0]["id"])
        raise RuntimeError("Failed to store payload in raw_data")

    @abstractmethod
    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the ingestion pipeline. Must be implemented by subclasses."""
        raise NotImplementedError

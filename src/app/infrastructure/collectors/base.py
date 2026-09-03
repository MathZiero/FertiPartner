"""Base Collector class for all FertiPartner data ingestion pipelines.

Handles collection auditing (data_collection_runs), immutable raw payload persistence (raw_data),
hash generation, and country/fertilizer foreign key caching.
"""

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

    def store_raw_payload(
        self,
        endpoint_url: str,
        payload_data: Any,
        source_id: int | None = None,
        collection_run_id: str | None = None,
        reference_date: str | None = None,
    ) -> int:
        """Store immutable raw payload in raw_data with sha256 hash and return row ID."""
        sid = source_id or self.source_id
        json_str = json.dumps(payload_data, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        insert_payload = {
            "source_id": sid,
            "collection_run_id": collection_run_id,
            "endpoint_url": endpoint_url,
            "payload_hash": payload_hash,
            "raw_payload": payload_data if isinstance(payload_data, dict) else {"data": payload_data},
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

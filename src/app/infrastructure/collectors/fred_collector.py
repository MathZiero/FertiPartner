"""Coletor de séries de preços e índices econômicos de fertilizantes (FRED - St. Louis Fed)."""

import logging
import os
from typing import Any, TypedDict
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_SOURCE_ID = 7  # FRED_FERT_PRICES in data_sources seed


class FredSeriesConfig(TypedDict, total=False):
    series_id: str
    fertilizer_slug: str
    benchmark_id: int
    price_type: str


DEFAULT_FRED_SERIES: list[FredSeriesConfig] = [
    {
        "series_id": "WPU0652013A6",
        "fertilizer_slug": "ureia",
        "benchmark_id": 2,  # US_GULF_UREA_FOB
        "price_type": "BENCHMARK",
    },
    {
        "series_id": "WPU0652026A",
        "fertilizer_slug": "dap",
        "benchmark_id": 4,  # US_GULF_DAP_FOB
        "price_type": "BENCHMARK",
    },
    {
        "series_id": "PCU325311325311",
        "fertilizer_slug": "ureia",
        "benchmark_id": 1,  # BALTIC_UREA_FOB
        "price_type": "BENCHMARK",
    },
    {
        "series_id": "DHHNGSP",
        "fertilizer_slug": "amonia-anidra",
        "benchmark_id": 8,  # US_HENRY_HUB_GAS
        "price_type": "SPOT",
    },
    {
        "series_id": "WPU065201",
        "fertilizer_slug": "ureia",
        "benchmark_id": 2,  # US_GULF_UREA_FOB
        "price_type": "SPOT",
    },
    {
        "series_id": "WPU065202",
        "fertilizer_slug": "dap",
        "benchmark_id": 4,  # US_GULF_DAP_FOB
        "price_type": "SPOT",
    },
    {
        "series_id": "WPU0652013A5",
        "fertilizer_slug": "ureia",
        "benchmark_id": 2,  # US_GULF_UREA_FOB
        "price_type": "CONTRACT",
    },
    {
        "series_id": "WPU06520201",
        "fertilizer_slug": "map",
        "benchmark_id": 4,  # US_GULF_DAP_FOB
        "price_type": "BENCHMARK",
    },
    {
        "series_id": "WPU06520202",
        "fertilizer_slug": "ssp",
        "benchmark_id": 4,  # US_GULF_DAP_FOB
        "price_type": "BENCHMARK",
    },
]


class FREDCollector(BaseCollector):
    """Ingestion collector for FRED commodity and PPI price series."""

    def __init__(
        self,
        api_key: str | None = None,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=1.0),
            source_id=FRED_SOURCE_ID,
        )
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED_API_KEY must be provided or configured in .env")

    def run(
        self,
        series_list: list[FredSeriesConfig] | list[dict[str, Any]] | None = None,
        start_date: str = "2020-01-01",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute FRED collection for configured series.

        Args:
            series_list: List of series configs to collect. Defaults to DEFAULT_FRED_SERIES.
            start_date: Initial observation date (YYYY-MM-DD). Defaults to '2020-01-01'.

        Returns:
            dict with execution summary.
        """
        targets = series_list or DEFAULT_FRED_SERIES
        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"series_count": len(targets), "start_date": start_date},
        )

        total_fetched = 0
        total_inserted = 0

        try:
            for target in targets:
                sid = str(target["series_id"])
                fert_slug = str(target["fertilizer_slug"])
                benchmark_id = int(target["benchmark_id"])
                price_type = str(target.get("price_type", "BENCHMARK"))

                fert_id = self.resolve_fertilizer_id(fert_slug)
                if not fert_id:
                    logger.warning("Fertilizer slug '%s' not found in database. Skipping %s.", fert_slug, sid)
                    continue

                logger.info("Fetching FRED series %s for %s...", sid, fert_slug)
                params = {
                    "series_id": sid,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "observation_start": start_date,
                }

                response = self.http.get(FRED_OBSERVATIONS_URL, params=params)
                data = response.json()
                observations = data.get("observations", [])
                total_fetched += len(observations)

                if not observations:
                    continue

                # Store raw payload
                raw_id = self.store_raw_payload(
                    endpoint_url=f"{FRED_OBSERVATIONS_URL}?series_id={sid}",
                    payload_data=data,
                    collection_run_id=run_id,
                    reference_date=observations[-1]["date"] if observations else None,
                )

                # Transform and insert normalized price_records
                rows_to_insert = []
                for obs in observations:
                    val_str = obs.get("value", "").strip()
                    if not val_str or val_str == ".":
                        continue
                    try:
                        price_val = float(val_str)
                    except ValueError:
                        continue

                    rows_to_insert.append({
                        "fertilizer_id": fert_id,
                        "benchmark_id": benchmark_id,
                        "price_date": obs["date"],
                        "frequency": "MONTHLY",
                        "price_type": price_type,
                        "original_price": price_val,
                        "currency_code": "USD",
                        "original_unit_code": "MT",
                        "standard_price_usd_per_mt": price_val,
                        "data_status": "OFFICIAL",
                        "source_id": self.source_id,
                        "raw_data_id": raw_id,
                    })

                if rows_to_insert:
                    # Upsert with on_conflict
                    res = (
                        self.supabase.table("price_records")
                        .upsert(
                            rows_to_insert,
                            on_conflict="fertilizer_id, benchmark_id, price_date, price_type, source_id",
                        )
                        .execute()
                    )
                    inserted_count = len(res.data) if res.data else len(rows_to_insert)
                    total_inserted += inserted_count
                    logger.info("Inserted/updated %d price records for %s", inserted_count, sid)

            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="SUCCESS",
            )
            return {
                "status": "SUCCESS",
                "run_id": run_id,
                "records_fetched": total_fetched,
                "records_inserted": total_inserted,
            }

        except Exception as exc:
            logger.exception("Error executing FRED collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

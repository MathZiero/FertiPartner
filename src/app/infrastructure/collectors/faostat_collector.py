"""Coletor de dados globais de produção e consumo de fertilizantes (FAOSTAT RFB)."""

import logging
from typing import Any
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.faostat.auth import FAOSTATAuthManager
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

FAOSTAT_DATA_URL = "https://faostatservices.fao.org/api/v1/en/data/RFB"
FAOSTAT_SOURCE_ID = 2  # FAOSTAT_RFB

# Item code to canonical fertilizer ID mapping
FAO_ITEM_FERTILIZER_MAP = {
    "4001": 1,  # Urea
    "4023": 2,  # MAP
    "4022": 3,  # DAP
    "4016": 4,  # Potassium chloride (muriate of potash / MOP / KCl)
}

# FAO Area Code to Country ISO2
FAO_AREA_TO_ISO2 = {
    "21": "BR",   # Brazil
    "231": "US",  # United States
    "41": "CN",   # China
    "100": "IN",  # India
    "185": "RU",  # Russian Federation
    "33": "CA",   # Canada
    "143": "MA",  # Morocco
    "57": "BY",   # Belarus
    "179": "QA",  # Qatar
    "194": "SA",  # Saudi Arabia
    "59": "EG",   # Egypt
    "9": "AR",    # Argentina
    "79": "DE",   # Germany
    "162": "NO",  # Norway
}


class FAOSTATCollector(BaseCollector):
    """Ingestion collector for FAOSTAT production and consumption records."""

    def __init__(
        self,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=2.0),
            source_id=FAOSTAT_SOURCE_ID,
        )
        self.auth_manager = FAOSTATAuthManager()

    def run(
        self,
        year: int = 2022,
        area_codes: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute FAOSTAT collection for specified year and areas.

        Args:
            year: Reference year (e.g. 2022).
            area_codes: FAOSTAT area codes. Defaults to top strategic producers/consumers.

        Returns:
            dict with execution summary.
        """
        areas = area_codes or list(FAO_AREA_TO_ISO2.keys())
        token = self.auth_manager.get_token()

        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"year": year, "areas_count": len(areas)},
        )

        headers = {"Authorization": f"Bearer {token}"}
        total_fetched = 0
        total_inserted = 0

        try:
            for area in areas:
                iso2 = FAO_AREA_TO_ISO2.get(area)
                country_id = self.resolve_country_id(iso2)
                if not country_id:
                    logger.debug("Area code %s (ISO %s) not in countries. Skipping.", area, iso2)
                    continue

                logger.info("Fetching FAOSTAT RFB for area=%s (ISO=%s), year=%d...", area, iso2, year)
                params = {
                    "area": area,
                    "year": str(year),
                }

                response = self.http.get(FAOSTAT_DATA_URL, headers=headers, params=params)
                data = response.json()
                items = data.get("data", [])
                total_fetched += len(items)

                if not items:
                    continue

                # Store raw payload
                raw_id = self.store_raw_payload(
                    endpoint_url=f"{FAOSTAT_DATA_URL}?area={area}&year={year}",
                    payload_data=data,
                    collection_run_id=run_id,
                    reference_date=f"{year}-12-31",
                )

                prod_rows = []
                consump_rows = []

                for item in items:
                    item_code = str(item.get("Item Code", "")).strip()
                    fert_id = FAO_ITEM_FERTILIZER_MAP.get(item_code)
                    if not fert_id:
                        continue

                    element = str(item.get("Element", "")).strip()
                    val_str = str(item.get("Value", "")).strip()
                    try:
                        qty_mt = float(val_str)
                    except ValueError:
                        continue

                    if element == "Production":
                        prod_rows.append({
                            "fertilizer_id": fert_id,
                            "country_id": country_id,
                            "period_start_date": f"{year}-01-01",
                            "period_end_date": f"{year}-12-31",
                            "period_type": "YEAR",
                            "data_status": "OFFICIAL",
                            "original_quantity": qty_mt,
                            "original_unit_code": "MT",
                            "standard_quantity_mt": qty_mt,
                            "source_id": self.source_id,
                            "raw_data_id": raw_id,
                        })
                    elif element in ("Agricultural Use", "Agriculture Use", "Use"):
                        consump_rows.append({
                            "fertilizer_id": fert_id,
                            "country_id": country_id,
                            "period_start_date": f"{year}-01-01",
                            "period_end_date": f"{year}-12-31",
                            "period_type": "YEAR",
                            "sector": "AGRICULTURE",
                            "original_quantity": qty_mt,
                            "original_unit_code": "MT",
                            "standard_quantity_mt": qty_mt,
                            "source_id": self.source_id,
                            "raw_data_id": raw_id,
                        })

                if prod_rows:
                    res = (
                        self.supabase.table("production_records")
                        .upsert(
                            prod_rows,
                            on_conflict="fertilizer_id, country_id, period_start_date, period_type, source_id",
                        )
                        .execute()
                    )
                    inserted_prod = len(res.data) if res.data else len(prod_rows)
                    total_inserted += inserted_prod
                    logger.info("Inserted %d production records for area %s", inserted_prod, area)


                if consump_rows:
                    res = (
                        self.supabase.table("consumption_records")
                        .upsert(
                            consump_rows,
                            on_conflict="fertilizer_id, country_id, period_start_date, period_type, sector, source_id",
                        )
                        .execute()
                    )
                    inserted_consump = len(res.data) if res.data else len(consump_rows)
                    total_inserted += inserted_consump
                    logger.info("Inserted %d consumption records for area %s", inserted_consump, area)

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
            logger.exception("Error executing FAOSTAT collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

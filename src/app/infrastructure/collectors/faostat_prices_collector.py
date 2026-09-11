"""Coletor de preços pagos por agricultores e preços ao produtor de fertilizantes (FAOSTAT PP)."""

import logging
from typing import Any
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.faostat.auth import FAOSTATAuthManager
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

FAOSTAT_PRICES_DATA_URL = "https://faostatservices.fao.org/api/v1/en/data/PP"
FAOSTAT_PP_SOURCE_ID = 9  # FAOSTAT_PP in data_sources seed

# Mapeamento de códigos de item da FAO (PP) para o ID canônico do fertilizante
FAO_PRICE_ITEM_FERTILIZER_MAP: dict[str, int] = {
    "4001": 1,   # Urea
    "3102": 1,   # Urea (HS / item alternativo)
    "4023": 2,   # Monoammonium phosphate (MAP)
    "4022": 3,   # Diammonium phosphate (DAP)
    "4016": 4,   # Potassium chloride (MOP / KCl)
    "4007": 5,   # Ammonia, anhydrous
    "4003": 6,   # Ammonium nitrate (AN)
    "4002": 7,   # Ammonium sulphate
    "4013": 8,   # Single Superphosphate (SSP)
    "4012": 9,   # Triple Superphosphate (TSP)
    "4011": 10,  # Phosphate rock
    "4017": 11,  # Potassium sulphate (SOP)
}

# Código de área FAO para ISO2
FAO_AREA_TO_ISO2: dict[str, str] = {
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


class FAOSTATInputPricesCollector(BaseCollector):
    """Ingestion collector for FAOSTAT input prices and farm-gate commodity costs."""

    def __init__(
        self,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=2.0),
            source_id=FAOSTAT_PP_SOURCE_ID,
        )
        self.auth_manager = FAOSTATAuthManager()

    def resolve_benchmark_id(self, area_code: str, fertilizer_id: int) -> int:
        """Determina o benchmark_id mais adequado no catálogo 4NF para o par (país, fertilizante)."""
        if area_code == "21":  # Brasil
            if fertilizer_id in (4, 11):  # Potássicos
                return 7  # BRAZIL_POTASH_CFR
            return 3  # BRAZIL_UREA_CFR

        if area_code == "33" and fertilizer_id in (4, 11):  # Canadá Potássio
            return 6  # VANCOUVER_POTASH_FOB

        if area_code == "143" and fertilizer_id in (2, 3, 8, 9, 10):  # Marrocos Fosfatos
            return 5  # MOROCCO_DAP_FOB

        # Regras gerais por categoria de nutriente
        if fertilizer_id in (2, 3, 8, 9, 10):  # Fosfatados
            return 4  # US_GULF_DAP_FOB
        if fertilizer_id in (4, 11):  # Potássicos
            return 6  # VANCOUVER_POTASH_FOB

        # Nitrogenados (padrão)
        return 2  # US_GULF_UREA_FOB

    def run(
        self,
        year: int = 2022,
        area_codes: list[str] | None = None,
        fertilizer_id: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute FAOSTAT PP price collection for specified year and areas.

        Args:
            year: Reference year (e.g. 2022).
            area_codes: List of FAOSTAT area codes (default: strategic countries).
            fertilizer_id: Optional fertilizer ID filter.

        Returns:
            dict with execution summary.
        """
        areas = area_codes or list(FAO_AREA_TO_ISO2.keys())
        token = self.auth_manager.get_token()

        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"year": year, "areas_count": len(areas), "fertilizer_id": fertilizer_id},
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        total_fetched = 0
        total_inserted = 0

        try:
            for area in areas:
                iso2 = FAO_AREA_TO_ISO2.get(area)
                logger.info("Fetching FAOSTAT PP prices for area=%s (ISO=%s), year=%d...", area, iso2, year)
                params = {
                    "area": area,
                    "year": str(year),
                }

                response = self.http.get(FAOSTAT_PRICES_DATA_URL, headers=headers, params=params)
                data = response.json()
                items = data.get("data", [])
                total_fetched += len(items)

                if not items:
                    continue

                # Armazena payload bruto para conformidade e auditoria 4NF
                raw_id = self.store_raw_payload(
                    endpoint_url=f"{FAOSTAT_PRICES_DATA_URL}?area={area}&year={year}",
                    payload_data=data,
                    collection_run_id=run_id,
                    reference_date=f"{year}-12-31",
                )

                rows_to_insert = []
                for item in items:
                    item_code = str(item.get("Item Code", "")).strip()
                    fert_id = FAO_PRICE_ITEM_FERTILIZER_MAP.get(item_code)
                    if not fert_id:
                        continue
                    if fertilizer_id is not None and fert_id != fertilizer_id:
                        continue

                    val_str = str(item.get("Value", "")).strip()
                    try:
                        price_val = float(val_str)
                    except ValueError:
                        continue

                    benchmark_id = self.resolve_benchmark_id(area_code=area, fertilizer_id=fert_id)

                    rows_to_insert.append({
                        "fertilizer_id": fert_id,
                        "benchmark_id": benchmark_id,
                        "price_date": f"{year}-12-01",
                        "frequency": "MONTHLY",
                        "price_type": "SPOT",
                        "original_price": price_val,
                        "currency_code": "USD",
                        "original_unit_code": "MT",
                        "standard_price_usd_per_mt": price_val,
                        "data_status": "OFFICIAL",
                        "source_id": self.source_id,
                        "raw_data_id": raw_id,
                    })

                if rows_to_insert:
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
                    logger.info("Inserted/updated %d price records for area %s", inserted_count, area)

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
            logger.exception("Error executing FAOSTAT Input Prices collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

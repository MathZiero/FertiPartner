"""Coletor de fluxos de comércio bilateral global de fertilizantes (UN Comtrade)."""

import logging
import os
from typing import Any, cast
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

COMTRADE_API_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
COMTRADE_SOURCE_ID = 3  # UN_COMTRADE in data_sources

# Canonical HS codes to fertilizer ID mapping
HS_FERTILIZER_MAP = {
    "310210": 1,  # Ureia
    "310520": 2,  # MAP / NPK
    "310530": 3,  # DAP
    "310420": 4,  # Cloreto de Potássio (KCl / MOP)
}


class UNComtradeCollector(BaseCollector):
    """Ingestion collector for UN Comtrade global trade records."""

    def __init__(
        self,
        api_key: str | None = None,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=2.0),
            source_id=COMTRADE_SOURCE_ID,
        )
        self.api_key = api_key or os.environ.get("COMTRADE_API_KEY")
        if not self.api_key:
            raise ValueError("COMTRADE_API_KEY must be provided or configured in .env")

        self._countries_by_numeric: dict[int, int] = {}
        self._load_numeric_codes()

    def _load_numeric_codes(self) -> None:
        """Cache numeric country codes (M49/UN) from database."""
        try:
            res = self.supabase.table("countries").select("id, numeric_code").execute()
            rows = cast(list[dict[str, Any]], res.data)
            if rows:
                for c in rows:
                    num = c.get("numeric_code")
                    if num is not None:
                        self._countries_by_numeric[int(num)] = int(c["id"])
        except Exception as exc:
            logger.warning("Failed to load numeric country codes: %s", exc)

    def run(
        self,
        period: int = 2023,
        reporter_codes: list[int] | None = None,
        cmd_codes: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute UN Comtrade collection for fertilizers.

        Args:
            period: Year of trade (e.g. 2023).
            reporter_codes: UN numeric reporter codes. Defaults to [76] (Brazil).
            cmd_codes: HS commodity codes. Defaults to all 4 fertilizer codes.

        Returns:
            dict with execution summary.
        """
        reporters = reporter_codes or [76]  # Brazil
        commodities = cmd_codes or list(HS_FERTILIZER_MAP.keys())

        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"period": period, "reporters": reporters, "commodities": commodities},
        )

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        total_fetched = 0
        total_inserted = 0

        try:
            for rep_code in reporters:
                rep_country_id = self._countries_by_numeric.get(rep_code)
                if not rep_country_id:
                    logger.warning("Reporter code %d not found in countries table. Skipping.", rep_code)
                    continue

                for cmd in commodities:
                    fert_id = HS_FERTILIZER_MAP.get(cmd)
                    if not fert_id:
                        continue

                    logger.info("Fetching UN Comtrade for reporter=%d, cmd=%s, period=%d...", rep_code, cmd, period)
                    params = {
                        "period": str(period),
                        "reporterCode": str(rep_code),
                        "cmdCode": cmd,
                    }

                    response = self.http.get(COMTRADE_API_URL, headers=headers, params=params)
                    data = response.json()
                    items = data.get("data", [])
                    total_fetched += len(items)

                    if not items:
                        continue

                    # Store raw payload
                    raw_id = self.store_raw_payload(
                        endpoint_url=f"{COMTRADE_API_URL}?period={period}&reporterCode={rep_code}&cmdCode={cmd}",
                        payload_data=data,
                        collection_run_id=run_id,
                        reference_date=f"{period}-12-31",
                    )

                    # Transform records
                    rows_to_insert = []
                    for item in items:
                        partner_num = item.get("partnerCode")
                        if not partner_num or int(partner_num) in (0, rep_code):
                            # Skip world total (0) or self-trade
                            continue

                        partner_country_id = self._countries_by_numeric.get(int(partner_num))
                        if not partner_country_id:
                            continue

                        flow_code = str(item.get("flowCode", "")).upper()
                        if flow_code == "M":
                            flow_type = "IMPORT"
                            exporter_id = partner_country_id
                            importer_id = rep_country_id
                        elif flow_code == "X":
                            flow_type = "EXPORT"
                            exporter_id = rep_country_id
                            importer_id = partner_country_id
                        else:
                            continue

                        if exporter_id == importer_id:
                            continue

                        val_usd = float(item.get("primaryValue") or 0.0)
                        net_wgt_kg = float(item.get("netWgt") or 0.0)
                        mt_val = round(net_wgt_kg / 1000.0, 4)

                        rows_to_insert.append({
                            "fertilizer_id": fert_id,
                            "flow_type": flow_type,
                            "exporter_country_id": exporter_id,
                            "importer_country_id": importer_id,
                            "period_start_date": f"{period}-01-01",
                            "period_end_date": f"{period}-12-31",
                            "period_type": "YEAR",
                            "original_quantity": net_wgt_kg,
                            "original_unit_code": "KG",
                            "standard_quantity_mt": mt_val,
                            "original_value": val_usd,
                            "currency_code": "USD",
                            "standard_value_usd": val_usd,
                            "incoterm": "FOB" if flow_type == "EXPORT" else "CIF",
                            "source_id": self.source_id,
                            "raw_data_id": raw_id,
                        })

                    if rows_to_insert:
                        # De-duplicate in memory before upserting
                        unique_rows = {}
                        for r in rows_to_insert:
                            key = (
                                r["fertilizer_id"],
                                r["flow_type"],
                                r["exporter_country_id"],
                                r["importer_country_id"],
                                r["period_start_date"],
                                r["period_type"],
                                r["source_id"],
                            )
                            unique_rows[key] = r

                        deduped_list = list(unique_rows.values())
                        res = (
                            self.supabase.table("trade_records")
                            .upsert(
                                deduped_list,
                                on_conflict="fertilizer_id, flow_type, exporter_country_id, importer_country_id, period_start_date, period_type, source_id",
                            )
                            .execute()
                        )
                        inserted_count = len(res.data) if res.data else len(deduped_list)
                        total_inserted += inserted_count
                        logger.info("Inserted %d bilateral records for HS %s", inserted_count, cmd)

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
            logger.exception("Error executing UN Comtrade collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

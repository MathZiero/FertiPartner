"""Coletor de dados de comércio exterior brasileiro (MDIC Comex Stat) para fertilizantes."""

import calendar
from datetime import datetime
import logging
import unicodedata
from typing import Any, cast
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

COMEX_API_URL = "https://api-comexstat.mdic.gov.br/general"
COMEX_IMP_SOURCE_ID = 4  # COMEXSTAT_IMP
COMEX_EXP_SOURCE_ID = 5  # COMEXSTAT_EXP

# Canonical NCM to Fertilizer ID mapping
NCM_FERTILIZER_MAP = {
    "31021010": 1,  # Ureia
    "31052000": 2,  # MAP
    "31053000": 3,  # DAP
    "31042090": 4,  # Cloreto de Potássio (KCl)
}

# Brazilian State Name to UF code
UF_MAP = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM", "bahia": "BA",
    "ceara": "CE", "distrito federal": "DF", "espirito santo": "ES", "goias": "GO",
    "maranhao": "MA", "mato grosso": "MT", "mato grosso do sul": "MS", "minas gerais": "MG",
    "para": "PA", "paraiba": "PB", "parana": "PR", "pernambuco": "PE", "piaui": "PI",
    "rio de janeiro": "RJ", "rio grande do norte": "RN", "rio grande do sul": "RS",
    "rondonia": "RO", "roraima": "RR", "santa catarina": "SC", "sao paulo": "SP",
    "sergipe": "SE", "tocantins": "TO", "nao declarada": "ND", "exterior": "EX",
}

# Mapping common partner countries to ISO codes for automatic insertion
COMMON_PARTNER_COUNTRIES = {
    "catar": ("QA", "QAT", 634),
    "russia": ("RU", "RUS", 643),
    "oma": ("OM", "OMN", 512),
    "nigeria": ("NG", "NGA", 566),
    "canada": ("CA", "CAN", 124),
    "egito": ("EG", "EGY", 818),
    "estados unidos": ("US", "USA", 840),
    "marrocos": ("MA", "MAR", 504),
    "china": ("CN", "CHN", 156),
    "belarus": ("BY", "BLR", 112),
    "alemanha": ("DE", "DEU", 276),
    "argelia": ("DZ", "DZA", 12),
    "israel": ("IL", "ISR", 376),
    "jordania": ("JO", "JOR", 400),
    "arabia saudita": ("SA", "SAU", 682),
    "trinidad e tobago": ("TT", "TTO", 780),
    "argentina": ("AR", "ARG", 32),
    "emirados arabes unidos": ("AE", "ARE", 784),
}


def normalize_str(s: str) -> str:
    """Normalize string removing accents and lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip().lower()


class ComexStatCollector(BaseCollector):
    """Ingestion collector for Brazilian Comex Stat (MDIC) fertilizer trade microdata."""

    def __init__(
        self,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=2.0, verify_ssl=False),
            source_id=COMEX_IMP_SOURCE_ID,
        )
        self.brazil_id = self.resolve_country_id("BR") or 1

    def _get_or_create_partner_country(self, country_name: str) -> int | None:
        """Find country ID or create new row in countries table if recognized."""
        clean_name = normalize_str(country_name)
        cid = self.resolve_country_id(country_name) or self.resolve_country_id(clean_name)
        if cid:
            return cid

        if clean_name in COMMON_PARTNER_COUNTRIES:
            iso2, iso3, num = COMMON_PARTNER_COUNTRIES[clean_name]
            try:
                res = (
                    self.supabase.table("countries")
                    .insert({
                        "iso2": iso2,
                        "iso3": iso3,
                        "numeric_code": num,
                        "name": country_name.strip(),
                        "region_id": 1,
                    })
                    .execute()
                )
                res_data = cast(list[dict[str, Any]], res.data)
                if res_data:
                    new_id = int(res_data[0]["id"])
                    self._countries_by_name[country_name.strip().lower()] = new_id
                    self._countries_by_name[clean_name] = new_id
                    self._countries_by_iso[iso2] = new_id
                    logger.info("Added new country: %s (%s, ID=%d)", country_name, iso2, new_id)
                    return new_id
            except Exception as exc:
                logger.debug("Country insertion ignored/existing: %s", exc)
                return self.resolve_country_id(iso2)

        return None

    def run(
        self,
        year: int = 2024,
        month_start: int = 1,
        month_end: int = 3,
        flow: str = "import",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute Comex Stat collection for fertilizers.

        Args:
            year: Year of trade (e.g. 2024).
            month_start: Initial month (1-12).
            month_end: Final month (1-12).
            flow: 'import' or 'export'.

        Returns:
            dict with execution metrics.
        """
        source_id = COMEX_IMP_SOURCE_ID if flow == "import" else COMEX_EXP_SOURCE_ID
        flow_type = "IMPORT" if flow == "import" else "EXPORT"

        period_from = f"{year}-{month_start:02d}"
        period_to = f"{year}-{month_end:02d}"

        run_id = self.start_collection_run(
            source_id=source_id,
            trigger_type="MANUAL",
            metadata={"year": year, "period": f"{period_from} to {period_to}", "flow": flow},
        )

        payload = {
            "flow": flow,
            "monthDetail": True,
            "period": {"from": period_from, "to": period_to},
            "filters": [{"filter": "ncm", "values": list(NCM_FERTILIZER_MAP.keys())}],
            "details": ["ncm", "country", "state"],
            "metrics": ["metricFOB", "metricKG"],
        }

        total_fetched = 0
        total_inserted = 0

        try:
            logger.info("Querying Comex Stat for %s (%s to %s)...", flow, period_from, period_to)
            response = self.http.post(COMEX_API_URL, json=payload)
            data = response.json()
            records = data.get("data", {}).get("list", [])
            total_fetched = len(records)
            logger.info("Received %d records from Comex Stat.", total_fetched)

            if not records:
                self.finish_collection_run(run_id, 0, 0, status="SUCCESS")
                return {"status": "SUCCESS", "run_id": run_id, "records_fetched": 0, "records_inserted": 0}

            # Store raw payload
            raw_id = self.store_raw_payload(
                endpoint_url=f"{COMEX_API_URL}?flow={flow}&period={period_from}_{period_to}",
                payload_data=data,
                source_id=source_id,
                collection_run_id=run_id,
                reference_date=f"{year}-{month_end:02d}-01",
            )

            # Process and aggregate records by unique bilateral key in 4NF
            aggregated_trades: dict[tuple, dict[str, Any]] = {}
            state_breakdowns: dict[tuple, list[dict[str, Any]]] = {}

            for item in records:
                ncm = str(item.get("coNcm", "")).strip()
                fert_id = NCM_FERTILIZER_MAP.get(ncm)
                if not fert_id:
                    continue

                country_name = item.get("country", "")
                partner_id = self._get_or_create_partner_country(country_name)
                if not partner_id:
                    logger.debug("Could not resolve country '%s', skipping record", country_name)
                    continue

                exporter_id = partner_id if flow == "import" else self.brazil_id
                importer_id = self.brazil_id if flow == "import" else partner_id

                if exporter_id == importer_id:
                    continue

                m_str = str(item.get("monthNumber", "01")).strip()
                m_int = int(m_str) if m_str.isdigit() else 1
                last_day = calendar.monthrange(year, m_int)[1]
                start_date = f"{year}-{m_int:02d}-01"
                end_date = f"{year}-{m_int:02d}-{last_day:02d}"

                kg_val = float(item.get("metricKG") or 0.0)
                fob_val = float(item.get("metricFOB") or 0.0)
                mt_val = round(kg_val / 1000.0, 4)

                key = (fert_id, flow_type, exporter_id, importer_id, start_date, "MONTH", source_id)

                if key not in aggregated_trades:
                    aggregated_trades[key] = {
                        "fertilizer_id": fert_id,
                        "flow_type": flow_type,
                        "exporter_country_id": exporter_id,
                        "importer_country_id": importer_id,
                        "period_start_date": start_date,
                        "period_end_date": end_date,
                        "period_type": "MONTH",
                        "original_quantity": kg_val,
                        "original_unit_code": "KG",
                        "standard_quantity_mt": mt_val,
                        "original_value": fob_val,
                        "currency_code": "USD",
                        "standard_value_usd": fob_val,
                        "incoterm": "FOB",
                        "source_id": source_id,
                        "raw_data_id": raw_id,
                    }
                    state_breakdowns[key] = []
                else:
                    aggregated_trades[key]["original_quantity"] += kg_val
                    aggregated_trades[key]["standard_quantity_mt"] += mt_val
                    aggregated_trades[key]["original_value"] += fob_val
                    aggregated_trades[key]["standard_value_usd"] += fob_val

                state_raw = item.get("state", "")
                uf_code = UF_MAP.get(normalize_str(state_raw), "ND")
                state_breakdowns[key].append({
                    "ncm_code": ncm,
                    "brazilian_state_uf": uf_code,
                })

            trade_rows_to_insert = list(aggregated_trades.values())
            logger.info("Aggregated %d microdata records into %d bilateral country-level trade facts.", len(records), len(trade_rows_to_insert))

            # Batch upsert into trade_records (in chunks of 100)
            chunk_size = 100
            for i in range(0, len(trade_rows_to_insert), chunk_size):
                chunk = trade_rows_to_insert[i:i + chunk_size]
                res = (
                    self.supabase.table("trade_records")
                    .upsert(
                        chunk,
                        on_conflict="fertilizer_id, flow_type, exporter_country_id, importer_country_id, period_start_date, period_type, source_id",
                    )
                    .execute()
                )
                res_data = cast(list[dict[str, Any]], res.data)
                if res_data:
                    inserted_batch = len(res_data)
                    total_inserted += inserted_batch

                    # Insert corresponding brazil_trade_details for the primary state of entry
                    details_batch = []
                    for idx, row_created in enumerate(res_data):
                        if idx >= len(chunk):
                            break
                        row_data = chunk[idx]
                        row_key = (
                            row_data["fertilizer_id"],
                            row_data["flow_type"],
                            row_data["exporter_country_id"],
                            row_data["importer_country_id"],
                            row_data["period_start_date"],
                            row_data["period_type"],
                            row_data["source_id"],
                        )
                        sub_details = state_breakdowns.get(row_key, [])
                        primary_uf = sub_details[0]["brazilian_state_uf"] if sub_details else "ND"
                        primary_ncm = sub_details[0]["ncm_code"] if sub_details else "31021010"
                        details_batch.append({
                            "trade_record_id": row_created["id"],
                            "ncm_code": primary_ncm,
                            "brazilian_state_uf": primary_uf,
                            "freight_value_usd": 0.0,
                        })

                    if details_batch:
                        self.supabase.table("brazil_trade_details").upsert(details_batch).execute()



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
            logger.exception("Error executing Comex Stat collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

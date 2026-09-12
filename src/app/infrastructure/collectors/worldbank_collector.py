"""Coletor de indicadores de desenvolvimento e consumo agrícola do Banco Mundial (World Bank Indicators API)."""

import logging
from typing import Any
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

WB_INDICATORS_BASE_URL = "https://api.worldbank.org/v2"
WB_INDICATORS_SOURCE_ID = 8  # WB_INDICATORS in data_sources

DEFAULT_WB_INDICATORS: dict[str, dict[str, str]] = {
    "AG.CON.FERT.ZS": {
        "name": "Fertilizer consumption (kilograms per hectare of arable land)",
        "unit_code": "KG_PER_HA",
    },
    "AG.CON.FERT.PT.ZS": {
        "name": "Fertilizer consumption (% of fertilizer production)",
        "unit_code": "PERCENT",
    },
}

# Países agrícolas estratégicos para análise macro de fertilizantes (ISO3)
DEFAULT_TOP_COUNTRIES_ISO3: list[str] = [
    "BRA", "USA", "CHN", "IND", "RUS", "CAN", "ARG", "DEU", "EGY", "FRA",
    "AUS", "IDN", "UKR", "POL", "MEX", "ZAF", "TUR", "VNM", "PAK", "BGD",
]


class WorldBankCollector(BaseCollector):
    """Ingestion collector for World Bank agricultural and fertilizer indicators."""

    def __init__(
        self,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=1.0),
            source_id=WB_INDICATORS_SOURCE_ID,
        )

    def run(
        self,
        indicator_id: str | None = None,
        country_codes: list[str] | None = None,
        start_year: int = 2015,
        end_year: int = 2023,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute World Bank indicator collection for configured indicators and countries.

        Args:
            indicator_id: Specific indicator code (e.g. 'AG.CON.FERT.ZS') or None for all defaults.
            country_codes: List of country ISO3 codes (e.g. ['BRA', 'USA']) or None for defaults.
            start_year: Start year for temporal window (default: 2015).
            end_year: End year for temporal window (default: 2023).

        Returns:
            dict with execution summary.
        """
        indicators_to_run = (
            {indicator_id: DEFAULT_WB_INDICATORS.get(indicator_id, {"name": indicator_id, "unit_code": "KG_PER_HA"})}
            if indicator_id
            else DEFAULT_WB_INDICATORS
        )
        countries = country_codes or DEFAULT_TOP_COUNTRIES_ISO3

        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={
                "indicators": list(indicators_to_run.keys()),
                "countries_count": len(countries),
                "year_range": f"{start_year}:{end_year}",
            },
        )

        total_fetched = 0
        total_inserted = 0

        try:
            # Consulta em blocos de países para otimizar chamadas HTTP
            country_arg = ";".join(countries)

            for ind_code, ind_meta in indicators_to_run.items():
                ind_name = ind_meta.get("name", ind_code)
                unit_code = ind_meta.get("unit_code", "KG_PER_HA")

                logger.info("Fetching World Bank indicator %s for %d countries...", ind_code, len(countries))
                endpoint_url = f"{WB_INDICATORS_BASE_URL}/country/{country_arg}/indicator/{ind_code}"
                params = {
                    "format": "json",
                    "per_page": 100,
                    "date": f"{start_year}:{end_year}",
                }

                page = 1
                total_pages = 1

                while page <= total_pages:
                    params["page"] = page
                    response = self.http.get(endpoint_url, params=params)
                    data = response.json()

                    # O World Bank retorna lista [metadata, observacoes] ou [mensagem_erro]
                    if not isinstance(data, list) or len(data) < 2:
                        logger.warning("Unexpected or empty response for %s: %s", ind_code, data)
                        break

                    meta = data[0] if isinstance(data[0], dict) else {}
                    total_pages = int(meta.get("pages", 1))
                    observations = data[1] if isinstance(data[1], list) else []
                    total_fetched += len(observations)

                    if not observations:
                        break

                    # Armazena payload bruto para rastreabilidade 4NF
                    raw_id = self.store_raw_payload(
                        endpoint_url=f"{endpoint_url}?date={start_year}:{end_year}&page={page}",
                        payload_data=data,
                        collection_run_id=run_id,
                        reference_date=f"{end_year}-12-31",
                    )

                    rows_to_insert = []
                    for obs in observations:
                        if not isinstance(obs, dict):
                            continue
                        raw_val = obs.get("value")
                        if raw_val is None:
                            continue

                        try:
                            val_float = float(raw_val)
                        except (ValueError, TypeError):
                            continue

                        iso3 = str(obs.get("countryiso3code") or obs.get("country", {}).get("id", "")).strip().upper()
                        country_id = self.resolve_country_id(iso3)
                        if not country_id:
                            # Tenta pelo nome do país
                            c_name = obs.get("country", {}).get("value")
                            country_id = self.resolve_country_id(c_name)

                        if not country_id:
                            logger.debug("Could not resolve country for WB obs: %s (%s)", iso3, obs.get("country"))
                            continue

                        try:
                            year_int = int(obs.get("date", 0))
                        except (ValueError, TypeError):
                            continue

                        rows_to_insert.append({
                            "country_id": country_id,
                            "indicator_code": ind_code,
                            "indicator_name": ind_name,
                            "year": year_int,
                            "value": val_float,
                            "unit_code": unit_code,
                            "data_status": "OFFICIAL",
                            "source_id": self.source_id,
                            "raw_data_id": raw_id,
                        })

                    if rows_to_insert:
                        res = (
                            self.supabase.table("country_indicators")
                            .upsert(
                                rows_to_insert,
                                on_conflict="country_id, indicator_code, year, source_id",
                            )
                            .execute()
                        )
                        inserted = len(res.data) if res.data else len(rows_to_insert)
                        total_inserted += inserted
                        logger.info("Upserted %d indicator rows for %s (page %d/%d)", inserted, ind_code, page, total_pages)

                    page += 1

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
            logger.exception("Error executing World Bank collector: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

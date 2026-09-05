"""Coletor de fluxos de comércio bilateral global de fertilizantes (UN Comtrade).

Suporta descoberta dinâmica de fertilizantes via banco de dados e ranqueamento
automático dos Top 10 países exportadores e importadores por produto.
"""

import logging
import os
from typing import Any, cast
from supabase import Client
from app.infrastructure.collectors.base import BaseCollector
from app.infrastructure.http import ResilientHttpClient

logger = logging.getLogger(__name__)

COMTRADE_DATA_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
COMTRADE_PREVIEW_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
COMTRADE_REFERENCE_URL = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
COMTRADE_SOURCE_ID = 3  # UN_COMTRADE in data_sources

# Mapeamento canônico padrão (usado como fallback seguro se o banco estiver indisponível)
DEFAULT_HS_FERTILIZER_MAP: dict[str, int] = {
    "310210": 1,  # Ureia
    "310540": 2,  # MAP
    "310520": 2,  # MAP / NPK
    "310530": 3,  # DAP
    "310420": 4,  # Cloreto de Potássio (KCl / MOP)
}


class UNComtradeCollector(BaseCollector):
    """Ingestion collector for UN Comtrade global trade records with dynamic Top Traders discovery."""

    def __init__(
        self,
        api_key: str | None = None,
        supabase_client: Client | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        super().__init__(
            supabase_client=supabase_client,
            http_client=http_client or ResilientHttpClient(min_interval_seconds=1.5),
            source_id=COMTRADE_SOURCE_ID,
        )
        self.api_key = api_key or os.environ.get("COMTRADE_API_KEY")
        if not self.api_key:
            raise ValueError("COMTRADE_API_KEY must be provided or configured in .env")

        self._countries_by_numeric: dict[int, int] = {}
        self._countries_by_iso2: dict[str, int] = {}
        self._partner_areas_ref: dict[int, dict[str, Any]] | None = None
        self.hs_fertilizer_map: dict[str, int] = {}

        self._load_numeric_codes()
        self._load_fertilizer_classifications()

    def _load_numeric_codes(self) -> None:
        """Cache numeric country codes (M49/UN) and ISO2 from database."""
        try:
            res = self.supabase.table("countries").select("id, numeric_code, iso2").execute()
            rows = cast(list[dict[str, Any]], res.data)
            if rows:
                for c in rows:
                    cid = int(c["id"])
                    num = c.get("numeric_code")
                    if num is not None:
                        self._countries_by_numeric[int(num)] = cid
                    iso2 = c.get("iso2")
                    if iso2:
                        self._countries_by_iso2[str(iso2).upper()] = cid
        except Exception as exc:
            logger.warning("Failed to load numeric country codes: %s", exc)

    def _load_fertilizer_classifications(self) -> None:
        """Carrega mapeamento dinâmico de códigos HS6 a partir da tabela fertilizer_classifications."""
        self.hs_fertilizer_map = dict(DEFAULT_HS_FERTILIZER_MAP)
        try:
            res = (
                self.supabase.table("fertilizer_classifications")
                .select("fertilizer_id, classification_code")
                .eq("classification_system", "HS6")
                .execute()
            )
            rows = cast(list[dict[str, Any]], res.data)
            if rows:
                for row in rows:
                    code = str(row.get("classification_code", "")).strip()
                    fert_id = row.get("fertilizer_id")
                    if code and fert_id:
                        self.hs_fertilizer_map[code] = int(fert_id)
                logger.info("Loaded %d dynamic HS6 classifications from database.", len(rows))
        except Exception as exc:
            logger.warning("Failed to load fertilizer classifications from database, using defaults: %s", exc)

    def _load_partner_areas_reference(self) -> dict[int, dict[str, Any]]:
        """Carrega a base de referência M49 da ONU para auto-cadastro de países."""
        if self._partner_areas_ref is not None:
            return self._partner_areas_ref

        ref_map: dict[int, dict[str, Any]] = {}
        try:
            resp = self.http.get(COMTRADE_REFERENCE_URL)
            if resp.status_code == 200:
                data = resp.json().get("results", [])
                for item in data:
                    pid = item.get("id") or item.get("PartnerCode")
                    if pid is not None and not item.get("isGroup", False):
                        ref_map[int(pid)] = item
                logger.info("Loaded %d reference countries from UN Comtrade partnerAreas.", len(ref_map))
        except Exception as exc:
            logger.warning("Could not fetch UN partnerAreas reference: %s", exc)

        self._partner_areas_ref = ref_map
        return ref_map

    def _ensure_country_exists(self, numeric_code: int) -> int | None:
        """Verifica se o país existe no banco ou insere automaticamente a partir do código M49."""
        if numeric_code in self._countries_by_numeric:
            return self._countries_by_numeric[numeric_code]

        ref_areas = self._load_partner_areas_reference()
        ref = ref_areas.get(numeric_code, {})

        iso2 = str(ref.get("PartnerCodeIsoAlpha2") or f"X{numeric_code % 90 + 10}").upper()[:2]
        iso3 = str(ref.get("PartnerCodeIsoAlpha3") or f"X{numeric_code:03d}").upper()[:3]
        name = str(ref.get("PartnerDesc") or ref.get("text") or f"Country {numeric_code}").strip()

        # 1. Se já conhecemos pelo código ISO2 (ex: US=840 no banco, mas UN reportou 842)
        if iso2 in self._countries_by_iso2:
            cid = self._countries_by_iso2[iso2]
            self._countries_by_numeric[numeric_code] = cid
            return cid

        # 2. Tentar inserir país se não existir
        try:
            res = (
                self.supabase.table("countries")
                .insert({
                    "numeric_code": int(numeric_code),
                    "iso2": iso2,
                    "iso3": iso3,
                    "name": name,
                    "region_id": 1,
                })
                .execute()
            )
            rows = cast(list[dict[str, Any]], res.data)
            if rows:
                new_id = int(rows[0]["id"])
                self._countries_by_numeric[numeric_code] = new_id
                self._countries_by_iso2[iso2] = new_id
                logger.info("Auto-registered country ID=%d: %s (%s, M49=%d)", new_id, name, iso2, numeric_code)
                return new_id
        except Exception as exc:
            logger.debug("Country insertion ignored/conflict for M49=%d (%s): %s", numeric_code, iso2, exc)
            try:
                check_res = (
                    self.supabase.table("countries")
                    .select("id, numeric_code, iso2")
                    .or_(f"numeric_code.eq.{numeric_code},iso2.eq.{iso2}")
                    .execute()
                )
                c_rows = cast(list[dict[str, Any]], check_res.data)
                if c_rows:
                    new_id = int(c_rows[0]["id"])
                    self._countries_by_numeric[numeric_code] = new_id
                    self._countries_by_iso2[iso2] = new_id
                    return new_id
            except Exception as search_exc:
                logger.debug("Fallback query failed for country M49=%d: %s", numeric_code, search_exc)

        # Cacheia None caso não tenha sido possível resolver para não re-tentar a cada linha
        self._countries_by_numeric[numeric_code] = None
        return None

    def discover_top_traders(
        self,
        cmd_code: str,
        period: int = 2023,
        top_n: int = 10,
    ) -> dict[str, list[dict[str, Any]]]:
        """Descobre os Top N países exportadores e Top N importadores para um código HS na ONU.

        Consulta o parceiro global (partnerCode=0) para ranquear por volume métrico (netWgt).
        """
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {
            "period": str(period),
            "cmdCode": str(cmd_code),
            "partnerCode": "0",
        }

        # Tenta endpoint de dados primeiro; se falhar, tenta preview
        endpoint = COMTRADE_DATA_URL
        response = self.http.get(endpoint, headers=headers, params=params)
        if response.status_code != 200:
            logger.warning("Data endpoint failed with %d, falling back to preview", response.status_code)
            endpoint = COMTRADE_PREVIEW_URL
            response = self.http.get(endpoint, headers=headers, params=params)

        data = response.json()
        items = data.get("data", [])

        imports: dict[int, dict[str, Any]] = {}
        exports: dict[int, dict[str, Any]] = {}

        for item in items:
            rep = item.get("reporterCode")
            if not rep or int(rep) == 0:
                continue

            rep_int = int(rep)
            flow = str(item.get("flowCode", "")).upper()
            qty = float(item.get("netWgt") or 0.0)
            val = float(item.get("primaryValue") or 0.0)
            qty_mt = qty / 1000.0

            if flow == "M":
                if rep_int not in imports:
                    imports[rep_int] = {"reporterCode": rep_int, "qty_mt": 0.0, "val_usd": 0.0}
                imports[rep_int]["qty_mt"] += qty_mt
                imports[rep_int]["val_usd"] += val
            elif flow == "X":
                if rep_int not in exports:
                    exports[rep_int] = {"reporterCode": rep_int, "qty_mt": 0.0, "val_usd": 0.0}
                exports[rep_int]["qty_mt"] += qty_mt
                exports[rep_int]["val_usd"] += val

        top_importers = sorted(imports.values(), key=lambda x: x["qty_mt"], reverse=True)[:top_n]
        top_exporters = sorted(exports.values(), key=lambda x: x["qty_mt"], reverse=True)[:top_n]

        logger.info(
            "Discovered %d top importers and %d top exporters for HS %s (year %d)",
            len(top_importers),
            len(top_exporters),
            cmd_code,
            period,
        )
        return {"importers": top_importers, "exporters": top_exporters}

    def run_auto_top_flows(
        self,
        period: int = 2023,
        top_n: int = 10,
        cmd_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Executa a descoberta automática de Top traders e coleta de fluxos bilaterais para todos os fertilizantes."""
        commodities = cmd_codes or list(self.hs_fertilizer_map.keys())

        run_id = self.start_collection_run(
            trigger_type="AUTOMATIC",
            metadata={"mode": "auto_top_traders", "period": period, "top_n": top_n, "commodities": commodities},
        )

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        total_fetched = 0
        total_inserted = 0

        try:
            for cmd in commodities:
                fert_id = self.hs_fertilizer_map.get(cmd)
                if not fert_id:
                    continue

                logger.info("=== Processando descoberta de Top %d para Fertilizante ID=%d (HS %s) ===", top_n, fert_id, cmd)
                top_traders = self.discover_top_traders(cmd_code=cmd, period=period, top_n=top_n)

                # Compilar conjunto de códigos de países estratégicos (Top Exportadores + Top Importadores + Brasil)
                target_reporters = {76}  # Brasil sempre monitorado
                for imp in top_traders["importers"]:
                    target_reporters.add(imp["reporterCode"])
                for exp in top_traders["exporters"]:
                    target_reporters.add(exp["reporterCode"])

                logger.info(
                    "Fertilizante ID=%d: Coletando fluxos bilaterais entre %d países chave",
                    fert_id,
                    len(target_reporters),
                )

                # Coletar fluxos para os países do grupo
                for rep_code in sorted(target_reporters):
                    rep_country_id = self._ensure_country_exists(rep_code)
                    if not rep_country_id:
                        logger.warning("Could not resolve reporter code %d, skipping", rep_code)
                        continue

                    params = {
                        "period": str(period),
                        "reporterCode": str(rep_code),
                        "cmdCode": cmd,
                    }

                    endpoint = COMTRADE_DATA_URL
                    response = self.http.get(endpoint, headers=headers, params=params)
                    if response.status_code != 200:
                        endpoint = COMTRADE_PREVIEW_URL
                        response = self.http.get(endpoint, headers=headers, params=params)

                    data = response.json()
                    items = data.get("data", [])
                    total_fetched += len(items)

                    if not items:
                        continue

                    raw_id = self.store_raw_payload(
                        endpoint_url=f"{endpoint}?period={period}&reporterCode={rep_code}&cmdCode={cmd}",
                        payload_data=data,
                        collection_run_id=run_id,
                        reference_date=f"{period}-12-31",
                    )

                    rows_to_insert = []
                    for item in items:
                        partner_num = item.get("partnerCode")
                        if not partner_num or int(partner_num) in (0, rep_code):
                            continue

                        partner_country_id = self._ensure_country_exists(int(partner_num))
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
            logger.exception("Error in auto top trade flows collection: %s", exc)
            self.finish_collection_run(
                run_id=run_id,
                records_fetched=total_fetched,
                records_inserted=total_inserted,
                status="FAILED",
                error_message=str(exc),
            )
            raise

    def run(
        self,
        period: int = 2023,
        reporter_codes: list[int] | None = None,
        cmd_codes: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute UN Comtrade collection for fertilizers with explicit reporter codes."""
        reporters = reporter_codes or [76]  # Brazil
        commodities = cmd_codes or list(self.hs_fertilizer_map.keys())

        run_id = self.start_collection_run(
            trigger_type="MANUAL",
            metadata={"period": period, "reporters": reporters, "commodities": commodities},
        )

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        total_fetched = 0
        total_inserted = 0

        try:
            for rep_code in reporters:
                rep_country_id = self._ensure_country_exists(rep_code)
                if not rep_country_id:
                    logger.warning("Reporter code %d could not be resolved. Skipping.", rep_code)
                    continue

                for cmd in commodities:
                    fert_id = self.hs_fertilizer_map.get(cmd)
                    if not fert_id:
                        continue

                    logger.info("Fetching UN Comtrade for reporter=%d, cmd=%s, period=%d...", rep_code, cmd, period)
                    params = {
                        "period": str(period),
                        "reporterCode": str(rep_code),
                        "cmdCode": cmd,
                    }

                    endpoint = COMTRADE_DATA_URL
                    response = self.http.get(endpoint, headers=headers, params=params)
                    if response.status_code != 200:
                        endpoint = COMTRADE_PREVIEW_URL
                        response = self.http.get(endpoint, headers=headers, params=params)

                    data = response.json()
                    items = data.get("data", [])
                    total_fetched += len(items)

                    if not items:
                        continue

                    raw_id = self.store_raw_payload(
                        endpoint_url=f"{endpoint}?period={period}&reporterCode={rep_code}&cmdCode={cmd}",
                        payload_data=data,
                        collection_run_id=run_id,
                        reference_date=f"{period}-12-31",
                    )

                    rows_to_insert = []
                    for item in items:
                        partner_num = item.get("partnerCode")
                        if not partner_num or int(partner_num) in (0, rep_code):
                            continue

                        partner_country_id = self._ensure_country_exists(int(partner_num))
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

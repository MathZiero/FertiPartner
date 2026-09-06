"""Script para expansão e harmonização dos dados mundiais de produção de fertilizantes (FAOSTAT/IFA).

Popula os principais países produtores globais e a produção nacional brasileira,
garantindo a integridade dos rankings e do cálculo de dependência externa.
"""

from pathlib import Path
import sys
import logging
from typing import Any, TypedDict, cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Garante execução no ambiente virtual do projeto (.venv) mesmo se chamado com o python global do sistema
venv_python = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
if venv_python.is_file() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    sys.exit(subprocess.call([str(venv_python)] + sys.argv))

sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from app.infrastructure.supabase.client import get_supabase_admin_client
from domain.benchmarks import PRODUCTION_BENCHMARKS, BenchmarkItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("expand_production_data")

SOURCE_ID_FAO = 2  # FAOSTAT_RFB


def main() -> None:
    client = get_supabase_admin_client()
    logger.info("Resolvendo IDs de países no Supabase...")

    res_c = client.table("countries").select("id, iso2").execute()
    countries_data = cast(list[dict[str, Any]], res_c.data or [])
    countries_map = {str(r["iso2"]): int(r["id"]) for r in countries_data if "iso2" in r and "id" in r}

    rows_to_upsert: list[dict[str, Any]] = []
    for item in PRODUCTION_BENCHMARKS:
        iso2 = item["iso2"]
        cid = countries_map.get(iso2)
        if not cid:
            logger.warning("País ISO %s não encontrado no banco. Pulando.", iso2)
            continue

        fert_id = item["fert_id"]
        for year, qty in item["years"].items():
            status = "OFFICIAL" if year == 2022 else "ESTIMATED"
            rows_to_upsert.append({
                "fertilizer_id": fert_id,
                "country_id": cid,
                "period_start_date": f"{year}-01-01",
                "period_end_date": f"{year}-12-31",
                "period_type": "YEAR",
                "original_quantity": qty,
                "original_unit_code": "MT",
                "standard_quantity_mt": qty,
                "data_status": status,
                "source_id": SOURCE_ID_FAO,
            })

    logger.info("Preparados %d registros de produção para inserção/upsert.", len(rows_to_upsert))

    res = (
        client.table("production_records")
        .upsert(
            rows_to_upsert,
            on_conflict="fertilizer_id, country_id, period_start_date, period_type, source_id",
        )
        .execute()
    )

    inserted = len(res.data) if res.data else len(rows_to_upsert)
    logger.info("Sucesso! %d registros de produção inseridos/atualizados em 4NF.", inserted)


if __name__ == "__main__":
    main()

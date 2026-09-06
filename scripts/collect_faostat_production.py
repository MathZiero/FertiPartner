"""Script CLI para coleta e povoamento de produção global de fertilizantes (FAOSTAT / IFA).

Obtém volumes físicos globais de síntese e mineração de fertilizantes (Ureia, MAP, DAP, KCl e Amônia)
a partir do domínio RFB da FAOSTAT ou aplica a consolidação mundial harmonizada de benchmarks (IFA/FAOSTAT),
populando a tabela production_records (e opcionalmente consumption_records) em 4NF.

Usage:
    python scripts/collect_faostat_production.py --year 2023
    python scripts/collect_faostat_production.py --year 2024 --offline-benchmarks
    python scripts/collect_faostat_production.py --year 2022 --include-consumption
    python scripts/collect_faostat_production.py --fertilizer ureia --dry-run
"""

import argparse
import logging
from pathlib import Path
import sys
import time
from typing import Any, cast

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

from app.infrastructure.collectors.faostat_collector import (
    FAOSTATCollector,
    FAO_AREA_TO_ISO2,
    FAO_ITEM_FERTILIZER_MAP,
    FAOSTAT_DATA_URL,
    FAOSTAT_SOURCE_ID,
)
from app.infrastructure.supabase.client import get_supabase_admin_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_faostat_production")


def run_offline_benchmarks(target_year: int | None = None, target_fert_id: int | None = None) -> int:
    """Popula benchmarks consolidados FAOSTAT/IFA para os principais produtores mundiais."""
    from domain.benchmarks import PRODUCTION_BENCHMARKS

    client = get_supabase_admin_client()
    print("\n[MODO BENCHMARK CONSOLIDADO] Sincronizando referências globais oficiais (IFA / FAOSTAT)...")

    res_c = client.table("countries").select("id, iso2").execute()
    countries_data = cast(list[dict[str, Any]], res_c.data or [])
    countries_map = {str(r["iso2"]): int(r["id"]) for r in countries_data if "iso2" in r and "id" in r}

    rows_to_upsert: list[dict[str, Any]] = []
    for item in PRODUCTION_BENCHMARKS:
        iso2 = item["iso2"]
        cid = countries_map.get(iso2)
        if not cid:
            continue

        fert_id = item["fert_id"]
        if target_fert_id is not None and fert_id != target_fert_id:
            continue
        for y, qty in item["years"].items():
            if target_year and y != target_year:
                continue
            status = "OFFICIAL" if y <= 2022 else "ESTIMATED"
            rows_to_upsert.append({
                "fertilizer_id": fert_id,
                "country_id": cid,
                "period_start_date": f"{y}-01-01",
                "period_end_date": f"{y}-12-31",
                "period_type": "YEAR",
                "original_quantity": qty,
                "original_unit_code": "MT",
                "standard_quantity_mt": qty,
                "data_status": status,
                "source_id": FAOSTAT_SOURCE_ID,
            })

    if not rows_to_upsert:
        print("Nenhum registro correspondente ao filtro selecionado.")
        return 0

    res = (
        client.table("production_records")
        .upsert(
            rows_to_upsert,
            on_conflict="fertilizer_id, country_id, period_start_date, period_type, source_id",
        )
        .execute()
    )
    inserted = len(res.data) if res.data else len(rows_to_upsert)
    print(f"[+] Inseridos/atualizados {inserted} fatos de produção global para o ano {target_year or 'todos'}.")
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor de Dados de Produção Mundial de Fertilizantes - FAOSTAT / IFA (FertiPartner)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Ano de referência da produção (padrão: 2023)",
    )
    parser.add_argument(
        "--fertilizer",
        type=str,
        default=None,
        help="Filtrar por fertilizante específico (ex: ureia, map, dap, kcl)",
    )
    parser.add_argument(
        "--areas",
        type=str,
        default=None,
        help="Lista de códigos de área FAO separados por vírgula (ex: 21,231,41,185)",
    )
    parser.add_argument(
        "--include-consumption",
        action="store_true",
        help="Coleta também registros de consumo agrícola (Agricultural Use)",
    )
    parser.add_argument(
        "--offline-benchmarks",
        action="store_true",
        help="Executa carga direta com a matriz mundial de produção consolidada (FAOSTAT/IFA/ANDA)",
    )
    parser.add_argument(
        "--fertilizer-id",
        type=int,
        default=None,
        help="ID do fertilizante específico para filtrar a coleta ou benchmarks",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa em modo de inspeção sem persistir no banco de dados",
    )

    args = parser.parse_args()

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - PRODUÇÃO GLOBAL DE FERTILIZANTES ({args.year})")
    print(f"Fonte: FAOSTAT RFB / IFA Benchmarks")
    print("=" * 75)

    if args.offline_benchmarks:
        t0 = time.time()
        if args.fertilizer_id is not None:
            inserted = run_offline_benchmarks(target_year=args.year, target_fert_id=args.fertilizer_id)
        else:
            inserted = run_offline_benchmarks(target_year=args.year)
        elapsed = time.time() - t0
        print(f"\nOperação concluída em {elapsed:.1f} segundos. Total inserido: {inserted} registros.\n")
        return

    collector = FAOSTATCollector()
    area_codes = [a.strip() for a in args.areas.split(",")] if args.areas else list(FAO_AREA_TO_ISO2.keys())

    print(f"\nPaíses/Áreas mapeados para consulta ({len(area_codes)} polos):")
    for a in area_codes[:8]:
        iso2 = FAO_AREA_TO_ISO2.get(a, "??")
        print(f"  * Área FAO {a:>3s} (ISO {iso2})")
    if len(area_codes) > 8:
        print(f"  ... e mais {len(area_codes) - 8} polos mundiais.")

    if args.dry_run:
        print("\n[MODO DRY-RUN] Verificando token de autenticação e disponibilidade da API da FAO...")
        try:
            token = collector.auth_manager.get_token()
            print(f"[+] Token FAOSTAT obtido com sucesso: {token[:12]}... (válido)")
            headers = {"Authorization": f"Bearer {token}"}
            sample_area = area_codes[0]
            resp = collector.http.get(
                FAOSTAT_DATA_URL,
                headers=headers,
                params={"area": sample_area, "year": str(args.year)},
            )
            items = resp.json().get("data", [])
            print(f"[+] Resposta recebida da FAOSTAT para área {sample_area}: {len(items)} registros brutos.")
        except Exception as exc:
            print(f"[!] Erro ao consultar API online da FAO: {exc}")
            print("[DICA] Você pode usar a flag '--offline-benchmarks' para povoamento seguro com os dados consolidados.")
        print("\nModo dry-run concluído sem alterações no banco.\n")
        return

    print("\nIniciando coleta online na API da FAOSTAT...")
    t0 = time.time()
    try:
        if args.fertilizer_id is not None:
            result = collector.run(year=args.year, area_codes=area_codes, fertilizer_id=args.fertilizer_id)
        else:
            result = collector.run(year=args.year, area_codes=area_codes)
        elapsed = time.time() - t0

        print("\n" + "=" * 75)
        print("COLETA FAOSTAT CONCLUÍDA COM SUCESSO!")
        print(f"Ano base: {args.year}")
        print(f"Status da execução: {result['status']}")
        print(f"Registros brutos obtidos: {result['records_fetched']:,}")
        print(f"Fatos de produção/consumo inseridos (4NF): {result['records_inserted']:,}")
        print(f"Tempo total: {elapsed:.1f} segundos")
        print("=" * 75 + "\n")
    except Exception as exc:
        logger.warning("Falha na coleta online da FAO (%s). Recorrendo à consolidação de benchmarks...", exc)
        print("\n[AVISO] API FAOSTAT indisponível ou token não renovado. Aplicando benchmarks mundiais consolidados...")
        if args.fertilizer_id is not None:
            run_offline_benchmarks(target_year=args.year, target_fert_id=args.fertilizer_id)
        else:
            run_offline_benchmarks(target_year=args.year)


if __name__ == "__main__":
    main()

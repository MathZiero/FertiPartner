"""Script CLI Agregador: Coleta de Dados Integrada por Fertilizante Único (FertiPartner).

Permite orquestrar a ingestão ou inspeção (dry-run) de dados para um fertilizante específico
a partir de todas as fontes oficiais integradas ao sistema:
  1. Comex Stat / MDIC (microdados aduaneiros brasileiros)
  2. FAOSTAT RFB (produção e consumo mundial)
  3. FRED / St. Louis Fed (benchmarks internacionais e índices de preços)
  4. UN Comtrade (top players globais e fluxos de comércio exterior)

Comportamento Resiliente:
  Falhas em APIs específicas (ex: timeout da FAO, limite de cota 403 da ONU)
  não interrompem a execução das demais fontes. O script produz um sumário executivo
  ao final reportando o status detalhado por fonte.

Usage:
    python scripts/collect_fertilizer_all_sources.py --fertilizer-id 1 --year 2024 --dry-run
    python scripts/collect_fertilizer_all_sources.py --id 2 --year 2023 --offline-benchmarks
    python scripts/collect_fertilizer_all_sources.py --fertilizer-id 1 --year 2024
"""

import argparse
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Garante execução no ambiente virtual do projeto (.venv) mesmo se chamado com o python global do sistema
venv_python = PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
if venv_python.is_file() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    sys.exit(subprocess.call([str(venv_python)] + sys.argv))

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from domain.fertilizers import FERTILIZERS_CATALOG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_fertilizer_all_sources")


def run_comex_stat_pipeline(
    fertilizer_id: int,
    year: int,
    dry_run: bool = False,
    flow: str = "both",
) -> dict[str, Any]:
    """Executa a coleta do MDIC Comex Stat para o fertilizante especificado."""
    from app.infrastructure.collectors.comex_stat_collector import (
        ComexStatCollector,
        NCM_FERTILIZER_MAP,
        COMEX_API_URL,
    )

    collector = ComexStatCollector()
    ncms = [n for n, fid in NCM_FERTILIZER_MAP.items() if fid == fertilizer_id]
    if not ncms:
        return {"status": "IGNORADO", "records": 0, "details": "Nenhum NCM mapeado"}

    flows = ["import", "export"] if flow == "both" else [flow]
    total_recs = 0

    if dry_run:
        for fl in flows:
            payload = {
                "flow": fl,
                "monthDetail": True,
                "period": {"from": f"{year}-01", "to": f"{year}-12"},
                "filters": [{"filter": "ncm", "values": ncms}],
                "details": ["ncm", "country", "state"],
                "metrics": ["metricFOB", "metricKG"],
            }
            resp = collector.http.post(COMEX_API_URL, json=payload)
            data = resp.json().get("data", {}).get("list", [])
            total_recs += len(data)
        return {"status": "SUCESSO", "records": total_recs, "details": f"NCM {', '.join(ncms)} (dry-run)"}

    for fl in flows:
        res = collector.run(year=year, month_start=1, month_end=12, flow=fl, ncms=ncms)
        total_recs += res.get("records_inserted", 0)

    return {"status": "SUCESSO", "records": total_recs, "details": f"NCM {', '.join(ncms)}"}


def run_faostat_pipeline(
    fertilizer_id: int,
    year: int,
    dry_run: bool = False,
    offline_benchmarks: bool = False,
    include_consumption: bool = False,
) -> dict[str, Any]:
    """Executa a coleta de produção/consumo na FAOSTAT ou aplica benchmarks consolidados."""
    from scripts.collect_faostat_production import run_offline_benchmarks

    if offline_benchmarks:
        inserted = run_offline_benchmarks(target_year=year, target_fert_id=fertilizer_id)
        return {"status": "SUCESSO", "records": inserted, "details": "Benchmarks consolidados FAOSTAT/IFA"}

    from app.infrastructure.collectors.faostat_collector import (
        FAOSTATCollector,
        FAO_AREA_TO_ISO2,
        FAO_ITEM_FERTILIZER_MAP,
        FAOSTAT_DATA_URL,
    )

    collector = FAOSTATCollector()
    area_codes = list(FAO_AREA_TO_ISO2.keys())

    if dry_run:
        token = collector.auth_manager.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = collector.http.get(
            FAOSTAT_DATA_URL,
            headers=headers,
            params={"area": area_codes[0], "year": str(year)},
        )
        items = resp.json().get("data", [])
        matched = [
            i for i in items
            if FAO_ITEM_FERTILIZER_MAP.get(str(i.get("Item Code", "")).strip()) == fertilizer_id
        ]
        return {"status": "SUCESSO", "records": len(matched), "details": f"{len(area_codes)} polos FAO (dry-run)"}

    try:
        res = collector.run(year=year, area_codes=area_codes, fertilizer_id=fertilizer_id)
        return {"status": "SUCESSO", "records": res.get("records_inserted", 0), "details": f"{len(area_codes)} polos FAO"}
    except Exception as exc:
        logger.warning("Falha na API online FAOSTAT (%s). Aplicando benchmarks de contingência...", exc)
        inserted = run_offline_benchmarks(target_year=year, target_fert_id=fertilizer_id)
        return {"status": "SUCESSO", "records": inserted, "details": "Fallback benchmarks FAOSTAT/IFA"}


def run_fred_pipeline(
    fertilizer_id: int,
    year: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executa a coleta de cotações e índices de preços internacionais no FRED."""
    from app.infrastructure.collectors.fred_collector import (
        FREDCollector,
        DEFAULT_FRED_SERIES,
        FRED_OBSERVATIONS_URL,
    )

    fert = next((f for f in FERTILIZERS_CATALOG if f["id"] == fertilizer_id), None)
    if not fert:
        return {"status": "IGNORADO", "records": 0, "details": "Fertilizante não cadastrado"}

    target_slug = fert["slug"].lower()
    targets = [s for s in DEFAULT_FRED_SERIES if s.get("fertilizer_slug", "").lower() == target_slug]
    if not targets:
        return {
            "status": "IGNORADO",
            "records": 0,
            "details": f"Nenhuma série internacional configurada para {fert['canonical_name']}",
        }

    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY não configurada no ambiente")

    collector = FREDCollector(api_key=api_key)
    series_ids = [s["series_id"] for s in targets]

    if dry_run:
        total_obs = 0
        for sid in series_ids:
            resp = collector.http.get(
                FRED_OBSERVATIONS_URL,
                params={
                    "series_id": sid,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": f"{year}-01-01",
                },
            )
            obs = resp.json().get("observations", [])
            total_obs += len(obs)
        return {"status": "SUCESSO", "records": total_obs, "details": f"Séries {', '.join(series_ids)} (dry-run)"}

    res = collector.run(series_list=targets, start_date=f"{year}-01-01")
    return {"status": "SUCESSO", "records": res.get("records_inserted", 0), "details": f"Séries {', '.join(series_ids)}"}


def run_comtrade_pipeline(
    fertilizer_id: int,
    year: int,
    dry_run: bool = False,
    top_n: int = 10,
) -> dict[str, Any]:
    """Executa a descoberta de top players e fluxos bilaterais na ONU (UN Comtrade)."""
    from app.infrastructure.collectors.comtrade_collector import UNComtradeCollector

    collector = UNComtradeCollector()
    hs_codes = [c for c, fid in collector.hs_fertilizer_map.items() if fid == fertilizer_id]
    if not hs_codes:
        return {"status": "IGNORADO", "records": 0, "details": "Nenhum código HS mapeado na ONU para este produto"}

    if dry_run:
        total_traders = 0
        for code in hs_codes:
            top = collector.discover_top_traders(cmd_code=code, period=year, top_n=top_n)
            total_traders += len(top.get("importers", [])) + len(top.get("exporters", []))
        return {
            "status": "SUCESSO",
            "records": total_traders,
            "details": f"HS {', '.join(hs_codes)} Top {top_n} (dry-run)",
        }

    res = collector.run_auto_top_flows(period=year, top_n=top_n, cmd_codes=hs_codes)
    return {
        "status": "SUCESSO",
        "records": res.get("records_inserted", 0),
        "details": f"HS {', '.join(hs_codes)} Top {top_n}",
    }


def run_worldbank_pipeline(
    year: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executa a coleta de indicadores de intensidade de fertilizantes no Banco Mundial."""
    from app.infrastructure.collectors.worldbank_collector import (
        WorldBankCollector,
        WB_INDICATORS_BASE_URL,
        DEFAULT_TOP_COUNTRIES_ISO3,
    )

    collector = WorldBankCollector()
    country_arg = ";".join(DEFAULT_TOP_COUNTRIES_ISO3[:5])

    if dry_run:
        url = f"{WB_INDICATORS_BASE_URL}/country/{country_arg}/indicator/AG.CON.FERT.ZS"
        params = {"format": "json", "per_page": 5, "date": f"{year}:{year}"}
        resp = collector.http.get(url, params=params)
        data = resp.json()
        obs = data[1] if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list) else []
        return {"status": "SUCESSO", "records": len(obs), "details": f"Indicadores WB (dry-run, ano {year})"}

    res = collector.run(start_year=year, end_year=year)
    return {"status": "SUCESSO", "records": res.get("records_inserted", 0), "details": f"Indicadores WB (ano {year})"}


def run_faostat_prices_pipeline(
    fertilizer_id: int,
    year: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Executa a coleta de preços pagos ao produtor no domínio PP do FAOSTAT."""
    from app.infrastructure.collectors.faostat_prices_collector import (
        FAOSTATInputPricesCollector,
        FAO_AREA_TO_ISO2,
        FAOSTAT_PRICES_DATA_URL,
        FAO_PRICE_ITEM_FERTILIZER_MAP,
    )

    collector = FAOSTATInputPricesCollector()
    area_codes = list(FAO_AREA_TO_ISO2.keys())

    if dry_run:
        token = collector.auth_manager.get_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        resp = collector.http.get(
            FAOSTAT_PRICES_DATA_URL,
            headers=headers,
            params={"area": area_codes[0], "year": str(year)},
        )
        data = resp.json()
        items = data.get("data", [])
        matched = [
            i for i in items
            if FAO_PRICE_ITEM_FERTILIZER_MAP.get(str(i.get("Item Code", "")).strip()) == fertilizer_id
        ]
        return {"status": "SUCESSO", "records": len(matched), "details": f"FAOSTAT PP {len(area_codes)} áreas (dry-run)"}

    res = collector.run(year=year, area_codes=area_codes, fertilizer_id=fertilizer_id)
    return {"status": "SUCESSO", "records": res.get("records_inserted", 0), "details": f"FAOSTAT PP {len(area_codes)} áreas"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor Agregador Multifonte por Fertilizante - FertiPartner"
    )
    parser.add_argument(
        "--fertilizer-id",
        "--id",
        dest="fertilizer_id",
        type=int,
        default=1,
        help="ID do fertilizante homologado (padrão: 1 para Ureia)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Ano de referência para a coleta (padrão: 2024)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo de inspeção sem efetuar gravação no banco de dados",
    )
    parser.add_argument(
        "--offline-benchmarks",
        action="store_true",
        help="Utiliza dados consolidados de produção (FAOSTAT/IFA)",
    )
    parser.add_argument(
        "--include-consumption",
        action="store_true",
        help="Inclui dados de consumo agrícola na FAOSTAT",
    )
    parser.add_argument(
        "--flow",
        choices=["import", "export", "both"],
        default="both",
        help="Fluxo comercial a consultar no MDIC Comex Stat (padrão: both)",
    )

    args = parser.parse_args()

    # Validação do ID informado contra o catálogo oficial
    fert = next((f for f in FERTILIZERS_CATALOG if f["id"] == args.fertilizer_id), None)
    if not fert:
        valid_ids = ", ".join(f"{f['id']} ({f['canonical_name']})" for f in FERTILIZERS_CATALOG)
        print(f"\n[ERRO] Fertilizante ID {args.fertilizer_id} não encontrado no catálogo oficial.")
        print(f"IDs disponíveis: {valid_ids}\n")
        sys.exit(1)

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - COLETOR MULTIFONTE INTEGRADO ({args.year})")
    print(f"Fertilizante : [ID {fert['id']}] {fert['canonical_name']} ({fert['chemical_formula']})")
    print(f"Categoria    : {fert.get('category_name', 'Fertilizante')}")
    print(f"Modo         : {'DRY-RUN (Inspeção)' if args.dry_run else 'INGESTÃO NOVO BANCO (4NF)'}")
    print("=" * 75)

    pipelines = [
        (
            "Comex Stat (MDIC)",
            run_comex_stat_pipeline,
            {"fertilizer_id": args.fertilizer_id, "year": args.year, "dry_run": args.dry_run, "flow": args.flow},
        ),
        (
            "FAOSTAT",
            run_faostat_pipeline,
            {
                "fertilizer_id": args.fertilizer_id,
                "year": args.year,
                "dry_run": args.dry_run,
                "offline_benchmarks": args.offline_benchmarks,
                "include_consumption": args.include_consumption,
            },
        ),
        (
            "FRED",
            run_fred_pipeline,
            {"fertilizer_id": args.fertilizer_id, "year": args.year, "dry_run": args.dry_run},
        ),
        (
            "UN Comtrade",
            run_comtrade_pipeline,
            {"fertilizer_id": args.fertilizer_id, "year": args.year, "dry_run": args.dry_run},
        ),
    ]

    results: dict[str, dict[str, Any]] = {}

    for source_name, pipeline_func, kwargs in pipelines:
        print(f"\n>> Executando coleta: {source_name}...")
        t_start = time.time()
        try:
            res = pipeline_func(**kwargs)
            results[source_name] = res
            status = res.get("status", "SUCESSO")
            recs = res.get("records", 0)
            details = res.get("details", "")
            print(f"   [{status}] {recs:,} registros - {details} ({time.time() - t_start:.1f}s)")
        except Exception as exc:
            logger.error("Erro na coleta %s: %s", source_name, exc)
            results[source_name] = {
                "status": "FALHA",
                "records": 0,
                "details": str(exc),
            }
            print(f"   [FALHA] {exc} ({time.time() - t_start:.1f}s)")

    # Relatório Consolidado Executivo
    print("\n" + "=" * 75)
    print("FERTIPARTNER - RELATÓRIO CONSOLIDADO DE COLETA INTEGRADA")
    print("=" * 75)
    print(f"Fertilizante : [ID {fert['id']}] {fert['canonical_name']} ({fert['chemical_formula']})")
    print(f"Categoria    : {fert.get('category_name', 'Fertilizante')}")
    print(f"Ano base     : {args.year}")
    print(f"Modo         : {'DRY-RUN (Inspeção)' if args.dry_run else 'INGESTÃO OFICIAL'}")
    print("-" * 75)
    print(f"{'Fonte':<22} | {'Status':<8} | {'Registros':>10} | Detalhes")
    print("-" * 75)

    for source_name, res in results.items():
        status = res.get("status", "N/A")
        recs = res.get("records", 0)
        details = res.get("details", "")
        print(f"{source_name:<22} | {status:<8} | {recs:>10,d} | {details}")

    print("-" * 75)

    total_sources = len(results)
    success_sources = sum(1 for r in results.values() if r.get("status") in ("SUCESSO", "IGNORADO"))
    failed_sources = sum(1 for r in results.values() if r.get("status") == "FALHA")

    if failed_sources == 0:
        status_geral = f"SUCESSO TOTAL ({success_sources}/{total_sources} fontes)"
    elif success_sources > 0:
        status_geral = f"SUCESSO PARCIAL ({success_sources}/{total_sources} fontes)"
    else:
        status_geral = f"FALHA TOTAL (0/{total_sources} fontes)"

    print(f"STATUS GERAL: {status_geral}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

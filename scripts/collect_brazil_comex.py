"""Script CLI para coleta e ingestão de microdados de comércio exterior brasileiro (MDIC Comex Stat).

Coleta registros mensais aduaneiros de importação e exportação de fertilizantes (NCMs de Ureia, MAP,
DAP, KCl) discriminados por país de origem/destino, UF de desembaraço, peso líquido (KG) e valor FOB ($ USD),
populando a base de dados normalizada em 4NF (trade_records e brazil_trade_details).

Usage:
    python scripts/collect_brazil_comex.py --year 2024 --flow import --month-start 1 --month-end 6
    python scripts/collect_brazil_comex.py --year 2023 --flow both
    python scripts/collect_brazil_comex.py --ncm 31021010 --year 2024 --dry-run
"""

import argparse
import logging
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

sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from app.infrastructure.collectors.comex_stat_collector import (
    ComexStatCollector,
    NCM_FERTILIZER_MAP,
    COMEX_API_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_brazil_comex")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor de Microdados de Comércio Exterior do Brasil - MDIC Comex Stat (FertiPartner)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Ano de referência das operações aduaneiras (padrão: 2024)",
    )
    parser.add_argument(
        "--flow",
        choices=["import", "export", "both"],
        default="both",
        help="Fluxo comercial a coletar: import, export ou both (padrão: import)",
    )
    parser.add_argument(
        "--month-start",
        type=int,
        default=1,
        help="Mês inicial do intervalo (1-12, padrão: 1)",
    )
    parser.add_argument(
        "--month-end",
        type=int,
        default=12,
        help="Mês final do intervalo (1-12, padrão: 12)",
    )
    parser.add_argument(
        "--ncm",
        type=str,
        default=None,
        help="Código NCM específico (ex: 31021010 para Ureia, 31052000 para MAP)",
    )
    parser.add_argument(
        "--fertilizer-id",
        type=int,
        default=None,
        help="ID do fertilizante específico para filtrar NCMs (ex: 1 para Ureia)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Consulta os dados na API pública do MDIC e exibe sumário sem gravar no banco de dados",
    )

    args = parser.parse_args()

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - COLETOR COMEX STAT / MDIC ({args.year})")
    print(f"Período: Meses {args.month_start:02d} a {args.month_end:02d} de {args.year}")
    print(f"Fluxo: {args.flow.upper()}")
    print("=" * 75)

    collector = ComexStatCollector()

    flows_to_run = ["import", "export"] if args.flow == "both" else [args.flow]
    if args.ncm:
        active_ncms = [args.ncm]
    elif args.fertilizer_id:
        active_ncms = [ncm for ncm, f_id in NCM_FERTILIZER_MAP.items() if f_id == args.fertilizer_id]
    else:
        active_ncms = list(NCM_FERTILIZER_MAP.keys())

    print("\nNCMs selecionados para monitoramento:")
    for ncm in active_ncms:
        fert_id = NCM_FERTILIZER_MAP.get(ncm, "Custom")
        print(f"  * NCM {ncm} -> Fertilizante ID {fert_id}")

    if args.dry_run:
        print("\n[MODO DRY-RUN / INSPEÇÃO] Consultando API pública do Comex Stat sem persistência...")
        for fl in flows_to_run:
            payload = {
                "flow": fl,
                "monthDetail": True,
                "period": {
                    "from": f"{args.year}-{args.month_start:02d}",
                    "to": f"{args.year}-{args.month_end:02d}",
                },
                "filters": [{"filter": "ncm", "values": active_ncms}],
                "details": ["ncm", "country", "state"],
                "metrics": ["metricFOB", "metricKG"],
            }
            resp = collector.http.post(COMEX_API_URL, json=payload)
            items = resp.json().get("data", {}).get("list", [])
            total_fob = sum(float(x.get("metricFOB", 0) or 0) for x in items)
            total_kg = sum(float(x.get("metricKG", 0) or 0) for x in items)

            print(f"\n[+] Resultados {fl.upper()} ({args.year}):")
            print(f"    - Registros aduaneiros retornados: {len(items):,}")
            print(f"    - Volume total: {total_kg / 1e6:,.2f} mil MT")
            print(f"    - Valor FOB total: $ {total_fob:,.2f} USD")
        print("\nOperação dry-run concluída com sucesso (nenhum registro foi alterado no banco).\n")
        return

    print("\nIniciando ingestão oficial e normalização em 4NF...")
    t0 = time.time()
    total_fetched = 0
    total_inserted = 0

    for fl in flows_to_run:
        print(f"\nProcessando fluxo '{fl}'...")
        kwargs = {}
        if args.ncm or args.fertilizer_id:
            kwargs["ncms"] = active_ncms

        res = collector.run(
            year=args.year,
            month_start=args.month_start,
            month_end=args.month_end,
            flow=fl,
            **kwargs,
        )
        total_fetched += res.get("records_fetched", 0)
        total_inserted += res.get("records_inserted", 0)

    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print("COLETA COMEX STAT CONCLUÍDA COM SUCESSO!")
    print(f"Ano base: {args.year}")
    print(f"Total de registros brutos obtidos: {total_fetched:,}")
    print(f"Fatos de comércio bilateral (4NF) inseridos/atualizados: {total_inserted:,}")
    print(f"Tempo total de execução: {elapsed:.1f} segundos")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

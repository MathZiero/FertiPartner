"""Script CLI para coleta dinâmica e auto-ajustável de fluxos de comércio internacional (Top N).

Identifica os maiores exportadores e importadores mundiais para cada fertilizante cadastrado
via UN Comtrade e popula o banco de dados em 4NF (trade_records) com as rotas bilaterais reais.

Usage:
    python scripts/collect_top_trade_flows.py --year 2023 --top-n 10
    python scripts/collect_top_trade_flows.py --hs 310210 --top-n 5
    python scripts/collect_top_trade_flows.py --discover-only
"""

import argparse
import logging
from pathlib import Path
import sys
import time

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

from app.infrastructure.collectors.comtrade_collector import UNComtradeCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_top_trade_flows")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor Dinâmico de Comércio Internacional FertiPartner (Top Exporters & Importers)"
    )
    parser.add_argument("--year", type=int, default=2023, help="Ano de referência (padrão: 2023)")
    parser.add_argument("--top-n", type=int, default=10, help="Quantidade de países no ranking por fluxo (padrão: 10)")
    parser.add_argument("--hs", type=str, default=None, help="Código HS específico (ex: 310210 para Ureia)")
    parser.add_argument("--fertilizer-id", type=int, default=None, help="ID do fertilizante específico para filtrar código HS")
    parser.add_argument("--discover-only", action="store_true", help="Apenas exibe os rankings dos maiores países sem gravar fluxos no banco")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(f"FERTIPARTNER - DESCOBERTA DINAMICA DE COMERCIO EXTERIOR ({args.year})")
    print(f"Top N: {args.top_n} maiores exportadores e importadores por produto")
    print("=" * 70)

    collector = UNComtradeCollector()
    if args.hs:
        cmd_codes = [args.hs]
    elif args.fertilizer_id:
        cmd_codes = [c for c, f_id in collector.hs_fertilizer_map.items() if f_id == args.fertilizer_id]
    else:
        cmd_codes = list(collector.hs_fertilizer_map.keys())

    print(f"\nFertilizantes cadastrados para processamento: {len(cmd_codes)}")
    for code in cmd_codes:
        fert_id = collector.hs_fertilizer_map.get(code)
        print(f"  * HS {code} -> Fertilizante ID {fert_id}")

    if args.discover_only:
        print("\n[MODO DESCOBERTA] Consultando rankings mundiais na ONU (partnerCode=0)...")
        for code in cmd_codes:
            fert_id = collector.hs_fertilizer_map.get(code)
            print(f"\n--- HS {code} (Fertilizante ID {fert_id}) ---")
            top = collector.discover_top_traders(cmd_code=code, period=args.year, top_n=args.top_n)

            print("\n[+] TOP IMPORTADORES:")
            for idx, c in enumerate(top["importers"], 1):
                print(f"  {idx:2d}. M49 {c['reporterCode']:<4d} | Volume: {c['qty_mt']:>12,.0f} MT | Valor: ${c['val_usd']:>14,.0f}")

            print("\n[+] TOP EXPORTADORES:")
            for idx, c in enumerate(top["exporters"], 1):
                print(f"  {idx:2d}. M49 {c['reporterCode']:<4d} | Volume: {c['qty_mt']:>12,.0f} MT | Valor: ${c['val_usd']:>14,.0f}")
        return

    print("\nIniciando ingestão completa e povoamento dos fluxos bilaterais...")
    t0 = time.time()
    result = collector.run_auto_top_flows(period=args.year, top_n=args.top_n, cmd_codes=cmd_codes)
    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print("COLETA CONCLUÍDA COM SUCESSO!")
    print(f"Status: {result['status']}")
    print(f"Run ID: {result['run_id']}")
    print(f"Registros brutos obtidos: {result['records_fetched']}")
    print(f"Fatos bilaterais inseridos/atualizados em 4NF: {result['records_inserted']}")
    print(f"Tempo total: {elapsed:.1f} segundos")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

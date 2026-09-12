"""Script CLI para ingestão e povoamento do banco de dados a partir de fontes externas.

Usage:
    python scripts/populate_database.py --all
    python scripts/populate_database.py --source fred
    python scripts/populate_database.py --source comex
    python scripts/populate_database.py --source comtrade
    python scripts/populate_database.py --source faostat
"""

import argparse
import logging
from pathlib import Path
import sys
import time

# Ensure src is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.infrastructure.collectors.comex_stat_collector import ComexStatCollector
from app.infrastructure.collectors.comtrade_collector import UNComtradeCollector
from app.infrastructure.collectors.faostat_collector import FAOSTATCollector
from app.infrastructure.collectors.faostat_prices_collector import FAOSTATInputPricesCollector
from app.infrastructure.collectors.fred_collector import FREDCollector
from app.infrastructure.collectors.worldbank_collector import WorldBankCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("populate_database")


def run_fred() -> None:
    print("\n" + "=" * 60)
    print("FASE 1: FRED - Séries Históricas de Preços e Índices")
    print("=" * 60)
    collector = FREDCollector()
    result = collector.run(start_date="2023-01-01")
    print(f"Sucesso: {result['records_inserted']} registros de preços inseridos. (Run ID: {result['run_id']})")


def run_comex() -> None:
    print("\n" + "=" * 60)
    print("FASE 2: COMEX STAT - Microdados de Comércio Exterior do Brasil")
    print("=" * 60)
    collector = ComexStatCollector()
    res_imp = collector.run(year=2024, month_start=1, month_end=6, flow="import")
    print(f"Importações: {res_imp['records_inserted']} fatos inseridos a partir de {res_imp['records_fetched']} linhas brutas.")


def run_comtrade(period: int = 2023, top_n: int = 10, auto_top: bool = True) -> None:
    print("\n" + "=" * 60)
    print(f"FASE 3: UN COMTRADE - Fluxos Globais de Comércio Bilateral (Top {top_n})")
    print("=" * 60)
    collector = UNComtradeCollector()
    if auto_top:
        result = collector.run_auto_top_flows(period=period, top_n=top_n)
    else:
        result = collector.run(period=period)
    print(f"Comtrade: {result['records_inserted']} fluxos inseridos a partir de {result['records_fetched']} linhas brutas.")


def run_faostat() -> None:
    print("\n" + "=" * 60)
    print("FASE 4: FAOSTAT - Produção e Consumo Mundial de Fertilizantes")
    print("=" * 60)
    collector = FAOSTATCollector()
    result = collector.run(year=2022, area_codes=["21", "231", "41", "185", "33", "143", "57", "179", "194", "59"])
    print(f"FAOSTAT: {result['records_inserted']} fatos inseridos a partir de {result['records_fetched']} linhas brutas.")


def run_worldbank() -> None:
    print("\n" + "=" * 60)
    print("FASE 5: BANCO MUNDIAL - Indicadores Agrícolas de Intensidade de Fertilizantes")
    print("=" * 60)
    collector = WorldBankCollector()
    result = collector.run(start_year=2018, end_year=2023)
    print(f"Banco Mundial: {result['records_inserted']} indicadores inseridos a partir de {result['records_fetched']} linhas brutas.")


def run_faostat_prices() -> None:
    print("\n" + "=" * 60)
    print("FASE 6: FAOSTAT PP - Preços de Fertilizantes Pagos por Produtores")
    print("=" * 60)
    collector = FAOSTATInputPricesCollector()
    result = collector.run(year=2022, area_codes=["21", "231", "41", "185", "33", "143", "57", "179", "194", "59"])
    print(f"FAOSTAT PP: {result['records_inserted']} preços inseridos a partir de {result['records_fetched']} linhas brutas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Povoamento do Banco de Dados FertiPartner (4NF)")
    parser.add_argument(
        "--source",
        choices=["fred", "comex", "comtrade", "faostat", "worldbank", "faostat_prices"],
        help="Executa fonte específica",
    )
    parser.add_argument("--all", action="store_true", help="Executa todas as fontes na ordem recomendada")
    parser.add_argument("--top-n", type=int, default=10, help="Top N exportadores e importadores para UN Comtrade (padrão: 10)")
    parser.add_argument("--year", type=int, default=2023, help="Ano de referência para UN Comtrade (padrão: 2023)")
    parser.add_argument("--brazil-only", action="store_true", help="Limita UN Comtrade apenas ao declarante Brasil")

    args = parser.parse_args()

    t0 = time.time()

    if args.all or not args.source:
        print("\nINICIANDO POVOAMENTO COMPLETO DO BANCO DE DADOS EM 4NF...")
        run_fred()
        time.sleep(2.0)
        run_comex()
        time.sleep(2.0)
        run_comtrade(period=args.year, top_n=args.top_n, auto_top=not args.brazil_only)
        time.sleep(2.0)
        run_faostat()
        time.sleep(2.0)
        run_worldbank()
        time.sleep(2.0)
        run_faostat_prices()
    elif args.source == "fred":
        run_fred()
    elif args.source == "comex":
        run_comex()
    elif args.source == "comtrade":
        run_comtrade(period=args.year, top_n=args.top_n, auto_top=not args.brazil_only)
    elif args.source == "faostat":
        run_faostat()
    elif args.source == "worldbank":
        run_worldbank()
    elif args.source == "faostat_prices":
        run_faostat_prices()

    elapsed = time.time() - t0
    print(f"\nOperação concluída em {elapsed:.1f} segundos!")


if __name__ == "__main__":
    main()

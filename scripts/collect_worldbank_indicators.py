"""Script CLI para ingestão de indicadores agrícolas e macroeconômicos do Banco Mundial (World Bank).

Coleta séries históricas de indicadores como consumo de fertilizantes por área arável (kg/ha)
e intensidade de consumo em relação à produção nacional a partir da World Bank Indicators API,
persistindo de forma normalizada em 4NF na tabela country_indicators.

Usage:
    python scripts/collect_worldbank_indicators.py --dry-run
    python scripts/collect_worldbank_indicators.py --indicator AG.CON.FERT.ZS --start-year 2018 --end-year 2023
    python scripts/collect_worldbank_indicators.py --countries BRA USA CHN
"""

import argparse
import logging
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Garante execução no ambiente virtual do projeto (.venv)
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

from app.infrastructure.collectors.worldbank_collector import (
    WorldBankCollector,
    DEFAULT_WB_INDICATORS,
    DEFAULT_TOP_COUNTRIES_ISO3,
    WB_INDICATORS_BASE_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_worldbank_indicators")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor de Indicadores Macroeconômicos e Agrícolas - Banco Mundial (FertiPartner)"
    )
    parser.add_argument(
        "--indicator",
        type=str,
        default=None,
        help="Código específico do indicador (ex: AG.CON.FERT.ZS para kg/ha, AG.CON.FERT.PT.ZS para % produção)",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=None,
        help="Lista de códigos ISO3 dos países (ex: --countries BRA USA CHN IND)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2015,
        help="Ano inicial da janela temporal (padrão: 2015)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2023,
        help="Ano final da janela temporal (padrão: 2023)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa a consulta na API do Banco Mundial e exibe amostras sem persistir no banco",
    )

    args = parser.parse_args()

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - BANCO MUNDIAL: INDICADORES AGRÍCOLAS ({args.start_year} - {args.end_year})")
    print(f"Fonte: World Bank World Development Indicators (WDI REST API)")
    print("=" * 75)

    collector = WorldBankCollector()
    target_countries = args.countries or DEFAULT_TOP_COUNTRIES_ISO3
    indicators = (
        {args.indicator: DEFAULT_WB_INDICATORS.get(args.indicator, {"name": args.indicator, "unit_code": "KG_PER_HA"})}
        if args.indicator
        else DEFAULT_WB_INDICATORS
    )

    print(f"\nIndicadores selecionados ({len(indicators)}):")
    for code, meta in indicators.items():
        print(f"  * {code}: {meta.get('name')}")
    print(f"Países selecionados ({len(target_countries)}): {', '.join(target_countries[:10])}{'...' if len(target_countries) > 10 else ''}")

    if args.dry_run:
        print(f"\n[MODO DRY-RUN] Consultando amostras na API do Banco Mundial sem gravar no banco...")
        country_sample = ";".join(target_countries[:3])
        for code in indicators:
            url = f"{WB_INDICATORS_BASE_URL}/country/{country_sample}/indicator/{code}"
            params = {
                "format": "json",
                "per_page": 5,
                "date": f"{args.start_year}:{args.end_year}",
            }
            resp = collector.http.get(url, params=params)
            data = resp.json()
            obs = data[1] if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list) else []
            print(f"\n[+] Indicador {code} (Amostra de {len(obs)} observações):")
            for item in obs[:3]:
                country_name = item.get("country", {}).get("value", "N/A")
                date_val = item.get("date")
                val = item.get("value")
                print(f"    - {country_name} ({date_val}): {val}")
        print("\nOperação dry-run concluída com sucesso (nenhuma alteração no banco).\n")
        return

    print("\nIniciando ingestão e persistência na tabela country_indicators...")
    t0 = time.time()
    result = collector.run(
        indicator_id=args.indicator,
        country_codes=target_countries,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print("COLETA DO BANCO MUNDIAL CONCLUÍDA COM SUCESSO!")
    print(f"Status: {result['status']}")
    print(f"Run ID: {result['run_id']}")
    print(f"Total de registros obtidos da API: {result['records_fetched']:,}")
    print(f"Indicadores gravados/atualizados em 4NF: {result['records_inserted']:,}")
    print(f"Tempo total de execução: {elapsed:.1f} segundos")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

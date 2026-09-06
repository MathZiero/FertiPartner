"""Script CLI para coleta de séries temporais de preços e benchmarks internacionais de fertilizantes (FRED).

Coleta séries históricas de preços FOB e índices PPI para os principais fertilizantes globais
(Ureia no Golfo dos EUA, Ureia no Mar Báltico, DAP no Golfo e Potássio) a partir do Federal Reserve
Economic Data (FRED - St. Louis Fed), normalizando para USD/MT e gravando na tabela price_records (4NF).

Usage:
    python scripts/collect_benchmark_prices.py --year 2023
    python scripts/collect_benchmark_prices.py --series WPU0652013A6 --year 2020
    python scripts/collect_benchmark_prices.py --fertilizer ureia --dry-run
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

sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from app.infrastructure.collectors.fred_collector import (
    FREDCollector,
    DEFAULT_FRED_SERIES,
    FRED_OBSERVATIONS_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_benchmark_prices")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor de Preços e Benchmarks Internacionais de Fertilizantes - FRED (FertiPartner)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Ano inicial para a série temporal de preços (padrão: 2023)",
    )
    parser.add_argument(
        "--series",
        type=str,
        default=None,
        help="ID específico da série FRED (ex: WPU0652013A6 para Ureia, WPU0652026A para DAP)",
    )
    parser.add_argument(
        "--fertilizer",
        type=str,
        default=None,
        help="Filtrar por fertilizante (ex: ureia, dap)",
    )
    parser.add_argument(
        "--fertilizer-id",
        type=int,
        default=None,
        help="ID do fertilizante específico (ex: 1 para Ureia, 3 para DAP)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Chave de API do FRED (caso não esteja configurada no .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Consulta observações mais recentes sem gravar no banco de dados",
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("FRED_API_KEY")
    if not api_key:
        print("\n[ERRO] Chave de API do FRED não configurada.")
        print("Configure a variável FRED_API_KEY no arquivo .env ou passe via argumento '--api-key SUA_CHAVE'.\n")
        sys.exit(1)

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - BENCHMARKS INTERNACIONAIS DE PREÇOS (A partir de {args.year})")
    print(f"Fonte: Federal Reserve Economic Data (FRED - St. Louis Fed)")
    print("=" * 75)

    collector = FREDCollector(api_key=api_key)

    target_slug = None
    if args.fertilizer_id:
        from domain.fertilizers import FERTILIZERS_CATALOG
        fert_item = next((f for f in FERTILIZERS_CATALOG if f["id"] == args.fertilizer_id), None)
        if fert_item:
            target_slug = fert_item["slug"].lower()
    elif args.fertilizer:
        target_slug = args.fertilizer.lower()

    # Filtragem das séries configuradas
    targets = list(DEFAULT_FRED_SERIES)
    if args.series:
        targets = [s for s in targets if s.get("series_id", "").upper() == args.series.upper()]
        if not targets:
            targets = [{
                "series_id": args.series,
                "fertilizer_slug": target_slug or "ureia",
                "benchmark_id": 1,
                "price_type": "BENCHMARK",
            }]
    elif target_slug:
        targets = [s for s in targets if s.get("fertilizer_slug", "").lower() == target_slug]

    print(f"\nSéries FRED selecionadas para coleta ({len(targets)} séries):")
    for s in targets:
        sid_label = s.get("series_id", "N/A")
        fert_label = s.get("fertilizer_slug", "N/A")
        print(f"  * Série {sid_label} -> Fertilizante '{fert_label}' (Benchmark ID {s.get('benchmark_id')})")

    start_date = f"{args.year}-01-01"

    if args.dry_run:
        print(f"\n[MODO DRY-RUN] Consultando observações na API do FRED desde {start_date}...")
        for target in targets:
            sid = str(target.get("series_id", ""))
            params = {
                "series_id": sid,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start_date,
            }
            resp = collector.http.get(FRED_OBSERVATIONS_URL, params=params)
            obs = resp.json().get("observations", [])
            print(f"\n[+] Série {sid}:")
            print(f"    - Observações encontradas: {len(obs)}")
            if obs:
                latest = obs[-1]
                print(f"    - Última cotação registrada: {latest.get('date')} -> $ {latest.get('value')} USD/MT")
        print("\nOperação dry-run concluída com sucesso (nenhuma alteração no banco).\n")
        return

    print(f"\nIniciando ingestão e persistência na tabela price_records...")
    t0 = time.time()
    result = collector.run(series_list=targets, start_date=start_date)
    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print("COLETA FRED CONCLUÍDA COM SUCESSO!")
    print(f"Status: {result['status']}")
    print(f"Run ID: {result['run_id']}")
    print(f"Total de cotações obtidas: {result['records_fetched']:,}")
    print(f"Registros de preços inseridos/atualizados (4NF): {result['records_inserted']:,}")
    print(f"Tempo total de execução: {elapsed:.1f} segundos")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

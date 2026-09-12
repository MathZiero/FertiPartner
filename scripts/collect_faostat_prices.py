"""Script CLI para ingestão de preços pagos por agricultores e preços ao produtor (FAOSTAT PP).

Coleta séries anuais de preços de fertilizantes ao nível de fazenda/produtor para os principais
países agrícolas a partir do domínio 'PP' da API do FAOSTAT, persistindo na tabela price_records (4NF).

Usage:
    python scripts/collect_faostat_prices.py --year 2022 --dry-run
    python scripts/collect_faostat_prices.py --year 2022 --fertilizer ureia
    python scripts/collect_faostat_prices.py --year 2022 --area-codes 21 231
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

from domain.fertilizers import FERTILIZERS_CATALOG
from app.infrastructure.collectors.faostat_prices_collector import (
    FAOSTATInputPricesCollector,
    FAO_AREA_TO_ISO2,
    FAOSTAT_PRICES_DATA_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collect_faostat_prices")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coletor de Preços de Fertilizantes ao Produtor - FAOSTAT PP (FertiPartner)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2022,
        help="Ano de referência para a coleta de preços (padrão: 2022)",
    )
    parser.add_argument(
        "--fertilizer",
        type=str,
        default=None,
        help="Slug do fertilizante específico (ex: ureia, dap, map, cloreto-de-potassio)",
    )
    parser.add_argument(
        "--fertilizer-id",
        type=int,
        default=None,
        help="ID do fertilizante específico no catálogo (ex: 1 para Ureia)",
    )
    parser.add_argument(
        "--area-codes",
        nargs="+",
        default=None,
        help="Lista de códigos de área FAO (ex: --area-codes 21 231 41)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Testa a consulta na API do FAOSTAT e exibe amostra sem gravar no banco de dados",
    )

    args = parser.parse_args()

    fert_id = args.fertilizer_id
    if not fert_id and args.fertilizer:
        slug = args.fertilizer.lower()
        fert_item = next((f for f in FERTILIZERS_CATALOG if f["slug"] == slug), None)
        if fert_item:
            fert_id = fert_item["id"]

    areas = args.area_codes or list(FAO_AREA_TO_ISO2.keys())

    print("\n" + "=" * 75)
    print(f"FERTIPARTNER - FAOSTAT PP: PREÇOS AO PRODUTOR / INSUMOS AGRÍCOLAS ({args.year})")
    print(f"Fonte: FAOSTAT Domain PP (Prices Paid / Producer Prices)")
    print("=" * 75)
    print(f"Ano: {args.year}")
    print(f"Áreas selecionadas ({len(areas)}): {', '.join(areas[:8])}{'...' if len(areas) > 8 else ''}")
    if fert_id:
        fert_name = next((f["canonical_name"] for f in FERTILIZERS_CATALOG if f["id"] == fert_id), str(fert_id))
        print(f"Filtro de fertilizante: {fert_name} (ID {fert_id})")

    collector = FAOSTATInputPricesCollector()

    if args.dry_run:
        print(f"\n[MODO DRY-RUN] Consultando amostras de preços no FAOSTAT (sem persistência)...")
        token = collector.auth_manager.get_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        sample_area = areas[0] if areas else "21"
        resp = collector.http.get(
            FAOSTAT_PRICES_DATA_URL,
            headers=headers,
            params={"area": sample_area, "year": str(args.year)},
        )
        data = resp.json()
        items = data.get("data", [])
        iso2 = FAO_AREA_TO_ISO2.get(sample_area, sample_area)
        print(f"\n[+] Área {sample_area} ({iso2}): {len(items)} cotações encontradas.")
        for item in items[:5]:
            item_name = item.get("Item", "N/A")
            val = item.get("Value", "N/A")
            elem = item.get("Element", "N/A")
            print(f"    - {item_name}: {val} USD/MT ({elem})")
        print("\nOperação dry-run concluída com sucesso (nenhuma alteração no banco).\n")
        return

    print("\nIniciando ingestão e persistência na tabela price_records...")
    t0 = time.time()
    result = collector.run(
        year=args.year,
        area_codes=areas,
        fertilizer_id=fert_id,
    )
    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print("COLETA FAOSTAT PREÇOS CONCLUÍDA COM SUCESSO!")
    print(f"Status: {result['status']}")
    print(f"Run ID: {result['run_id']}")
    print(f"Total de cotações obtidas: {result['records_fetched']:,}")
    print(f"Registros de preços inseridos/atualizados (4NF): {result['records_inserted']:,}")
    print(f"Tempo total de execução: {elapsed:.1f} segundos")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()

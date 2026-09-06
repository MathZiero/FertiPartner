"""Script CLI para gestão, sincronização e inspeção do catálogo mestre de fertilizantes.

Administra o cadastro técnico, agronômico e aduaneiro dos fertilizantes homologados na plataforma
FertiPartner (Ureia, MAP, DAP, KCl, Amônia Anidra, etc.), com fórmulas químicas, números de CAS,
garantias nutricionais mínimas e códigos aduaneiros (NCM/HS).

Usage:
    python scripts/populate_fertilizer_catalog.py --show
    python scripts/populate_fertilizer_catalog.py --sync-db --year 2024
    python scripts/populate_fertilizer_catalog.py --export-json catalog_dump.json
"""

import argparse
import json
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("streamlit").setLevel(logging.ERROR)

from domain.fertilizers import FERTILIZERS_CATALOG
from app.infrastructure.supabase.client import get_supabase_admin_client

logger = logging.getLogger("populate_fertilizer_catalog")


CATEGORIES_SEED = [
    {"id": 1, "code": "NITROGENOUS", "name": "Fertilizantes Nitrogenados", "description": "Produtos ricos em Nitrogênio (N) essenciais para crescimento vegetativo."},
    {"id": 2, "code": "PHOSPHATIC", "name": "Fertilizantes Fosfatados", "description": "Produtos ricos em Fósforo (P2O5) fundamentais para desenvolvimento radicular e energia celular."},
    {"id": 3, "code": "POTASSIC", "name": "Fertilizantes Potássicos", "description": "Produtos ricos em Potássio (K2O) para tolerância hídrica, enchimento de grãos e qualidade."},
    {"id": 4, "code": "NPK_MIXTURES", "name": "Misturas e Complexos NPK", "description": "Fertilizantes formulados combinando dois ou mais macronutrientes primários."},
    {"id": 5, "code": "MICRONUTRIENTS", "name": "Micronutrientes", "description": "Nutrientes de demanda em pequenas frações (Zn, B, Cu, Mn, Mo, Fe)."},
    {"id": 6, "code": "SECONDARY_MACRONUTRIENTS", "name": "Macronutrientes Secundários", "description": "Nutrientes requeridos em volumes intermediários (Enxofre, Cálcio e Magnésio)."},
]


def resolve_category_id(category_name: str) -> int:
    """Mapeia o nome da categoria para o ID canônico correspondente."""
    if "Nitrogenados" in category_name:
        return 1
    if "Fosfatados" in category_name:
        return 2
    if "Potássicos" in category_name:
        return 3
    if "Misturas" in category_name or "NPK" in category_name:
        return 4
    if "Micronutrientes" in category_name:
        return 5
    if "Secundários" in category_name or "Enxofre" in category_name:
        return 6
    return 1


def show_catalog() -> None:
    """Exibe o catálogo homologado em formato tabular formatado no terminal."""
    print("\n" + "=" * 105)
    print("FERTIPARTNER - CATÁLOGO OFICIAL DE FERTILIZANTES HOMOLOGADOS")
    print("=" * 105)
    header = f"{'ID':<3} | {'Nome Canônico':<34} | {'Categoria':<28} | {'Fórmula':<14} | {'CAS RN':<11}"
    print(header)
    print("-" * 105)
    for fert in FERTILIZERS_CATALOG:
        print(
            f"{fert['id']:<3d} | {fert['canonical_name'][:34]:<34} | {fert['category_name'][:28]:<28} | {fert.get('chemical_formula', '-'):<14} | {fert.get('cas_rn', '-'):<11}"
        )
    print("=" * 105)
    print(f"Total de produtos homologados: {len(FERTILIZERS_CATALOG)}\n")


def sync_database(year: int = 2024) -> None:
    """Sincroniza os registros de categorias e fertilizantes no banco de dados Supabase."""
    print(f"\nSincronizando {len(CATEGORIES_SEED)} categorias e {len(FERTILIZERS_CATALOG)} fertilizantes no Supabase (Ano {year})...")
    client = get_supabase_admin_client()

    # 1. Sincroniza categorias de fertilizantes (incluindo Macronutrientes Secundários e Micronutrientes)
    client.table("fertilizer_categories").upsert(CATEGORIES_SEED, on_conflict="id").execute()

    # 2. Sincroniza catálogo de fertilizantes
    rows = []
    for f in FERTILIZERS_CATALOG:
        rows.append({
            "id": f["id"],
            "slug": f["slug"],
            "canonical_name": f["canonical_name"],
            "category_id": resolve_category_id(f["category_name"]),
            "cas_rn": f.get("cas_rn"),
            "chemical_formula": f.get("chemical_formula"),
            "description": f.get("description"),
            "is_active": True,
        })

    res = client.table("fertilizers").upsert(rows, on_conflict="id").execute()
    inserted = len(res.data) if res.data else len(rows)
    print(f"[+] Sucesso! {inserted} fertilizantes sincronizados com o banco de dados.")

    # 3. Sincroniza classificações tarifárias (HS6 e NCM8)
    classif_rows = []
    for f in FERTILIZERS_CATALOG:
        fid = f["id"]
        for c in f.get("hs_ncm_codes", []):
            code_str = str(c).strip().replace(".", "")
            sys_name = "HS6" if len(code_str) == 6 else "NCM8"
            classif_rows.append({
                "fertilizer_id": fid,
                "classification_system": sys_name,
                "classification_code": code_str,
                "description": f["canonical_name"],
            })
    if classif_rows:
        res_cl = client.table("fertilizer_classifications").upsert(
            classif_rows,
            on_conflict="classification_system, classification_code, fertilizer_id",
        ).execute()
        n_cl = len(res_cl.data) if res_cl.data else len(classif_rows)
        print(f"[+] Sucesso! {n_cl} classificações tarifárias (HS/NCM) sincronizadas.\n")


def export_json(output_path: str) -> None:
    """Exporta o catálogo em formato JSON estruturado."""
    path = Path(output_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(FERTILIZERS_CATALOG, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Catálogo exportado com sucesso para: {path.resolve()} ({len(FERTILIZERS_CATALOG)} itens)\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gestão e Povoamento do Catálogo Oficial de Fertilizantes (FertiPartner)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Exibe o catálogo completo formatado no console",
    )
    parser.add_argument(
        "--sync-db",
        action="store_true",
        help="Sincroniza os dados do catálogo com o banco de dados Supabase",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Ano de referência da revisão do catálogo (padrão: 2024)",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Caminho do arquivo JSON de destino para exportação do catálogo",
    )

    args = parser.parse_args()

    if args.export_json:
        export_json(args.export_json)
    elif args.sync_db:
        sync_database(year=args.year)
    else:
        show_catalog()


if __name__ == "__main__":
    main()

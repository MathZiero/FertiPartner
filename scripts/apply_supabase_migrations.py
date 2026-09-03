"""Utilitário de linha de comando para aplicar e validar migrações SQL no Supabase."""

import argparse
import logging
import os
from pathlib import Path
import sys

# Ensure 'src' is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.infrastructure.supabase import (
    SupabaseClientManager,
    SupabaseConfig,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("apply_supabase_migrations")


def get_schema_file_path() -> Path:
    """Return the primary 4NF schema file path."""
    schema_path = PROJECT_ROOT / "infrastructure" / "supabase" / "schema.sql"
    if not schema_path.exists():
        schema_path = (
            PROJECT_ROOT
            / "infrastructure"
            / "supabase"
            / "migrations"
            / "20260902_000001_initial_schema_4nf.sql"
        )
    return schema_path


def check_connection(config: SupabaseConfig) -> bool:
    """Verify connectivity with Supabase REST API."""
    logger.info("Testando conectividade com Supabase em %s...", config.url)
    try:
        client = SupabaseClientManager.get_client(config)
        # Attempt to query fertilizers catalog table
        repo = SupabaseFertilizerRepository(client=client)
        fertilizers = repo.find_all(limit=5)
        logger.info(
            "Conexão bem-sucedida! Fertilizantes encontrados no catálogo: %d",
            len(fertilizers),
        )
        for fert in fertilizers:
            logger.info(" - [%s] %s", fert.get("slug", "N/A"), fert.get("canonical_name", "N/A"))
        return True
    except Exception as exc:
        logger.warning(
            "Aviso de verificação REST (tabelas podem ainda não ter sido criadas no Supabase): %s",
            exc,
        )
        return False


def apply_via_postgres_connection(db_url: str, schema_sql: str) -> bool:
    """Apply DDL directly using standard PostgreSQL connection string."""
    logger.info("Executando DDL via conexão direta PostgreSQL...")
    try:
        import psycopg  # type: ignore
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        logger.info("Migração 4NF executada com sucesso via psycopg!")
        return True
    except ImportError:
        pass

    try:
        import psycopg2  # type: ignore
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.close()
        logger.info("Migração 4NF executada com sucesso via psycopg2!")
        return True
    except ImportError:
        logger.error(
            "Nem psycopg nem psycopg2 estão instalados no ambiente para conexão direta Postgres."
        )
        return False
    except Exception as exc:
        logger.error("Erro executando migração via conexão direta: %s", exc)
        return False


def print_instructions(schema_path: Path) -> None:
    """Print step-by-step instructions for Supabase Web SQL Editor execution."""
    print("\n" + "=" * 80)
    print("INSTRUÇÕES PARA APLICAÇÃO DO SCHEMA 4NF NO SUPABASE")
    print("=" * 80)
    print(f"\n1. O script DDL modular e idempotente está localizado em:")
    print(f"   {schema_path}")
    print("\n2. Como aplicar com 1 clique no Supabase Dashboard:")
    print("   a) Acesse https://supabase.com/dashboard")
    print("   b) Abra seu projeto ('ghfbgcrvetskgntazdut')")
    print("   c) No menu lateral esquerdo, clique no ícone 'SQL Editor'")
    print("   d) Clique em '+ New query'")
    print("   e) Copie e cole todo o conteúdo do arquivo 'infrastructure/supabase/schema.sql'")
    print("   f) Clique no botão verde 'RUN'")
    print("\n3. Todas as tabelas em 4NF, constraints, índices, views analíticas,")
    print("   políticas RLS e dados iniciais (seed data) serão criados com sucesso.")
    print("=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aplicar e verificar schema 4NF no Supabase.")
    parser.add_argument(
        "--instructions-only",
        action="store_true",
        help="Apenas exibir instruções de aplicação no painel Supabase",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL"),
        help="String de conexão PostgreSQL direta (ex: postgresql://postgres:senha@db.ref.supabase.co:5432/postgres)",
    )
    args = parser.parse_args()

    schema_path = get_schema_file_path()

    if args.instructions_only:
        print_instructions(schema_path)
        return

    try:
        config = SupabaseConfig.from_env()
    except Exception as exc:
        logger.error("Erro ao carregar configurações do Supabase: %s", exc)
        print_instructions(schema_path)
        return

    if args.db_url:
        schema_sql = schema_path.read_text(encoding="utf-8")
        success = apply_via_postgres_connection(args.db_url, schema_sql)
        if success:
            check_connection(config)
            return

    # Check REST connection
    connected = check_connection(config)
    if not connected:
        print_instructions(schema_path)
    else:
        logger.info("Schema validado com sucesso no Supabase!")


if __name__ == "__main__":
    main()

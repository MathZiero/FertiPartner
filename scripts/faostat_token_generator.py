"""Command-line utility to generate, refresh, and inspect FAOSTAT tokens.

Usage:
    python scripts/faostat_token_generator.py
    python scripts/faostat_token_generator.py --check
    python scripts/faostat_token_generator.py --login --username user@example.com --password mypass
"""

import argparse
from datetime import datetime, timezone
import getpass
import os
from pathlib import Path
import sys

# Ensure src is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.infrastructure.faostat.auth import (
    FAOSTATAuthManager,
    decode_jwt_payload,
    is_token_valid,
)


def inspect_current_token() -> None:
    """Print details of the token currently in .env."""
    manager = FAOSTATAuthManager()
    token = manager.current_token

    print("\n" + "=" * 70)
    print("STATUS DO TOKEN FAOSTAT")
    print("=" * 70)

    if not token:
        print("Nenhum FAOSTAT_TOKEN encontrado no arquivo .env.")
        print("=" * 70 + "\n")
        return

    payload = decode_jwt_payload(token)
    if not payload:
        print("FAOSTAT_TOKEN presente, mas não foi possível decodificar o payload JWT.")
        print("=" * 70 + "\n")
        return

    username = payload.get("username", "N/A")
    exp_ts = payload.get("exp")
    iat_ts = payload.get("iat")

    print(f"Usuário / Sub: {username}")

    if iat_ts:
        iat_dt = datetime.fromtimestamp(iat_ts, tz=timezone.utc)
        print(f"Emitido em (UTC): {iat_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    if exp_ts:
        exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        now_ts = datetime.now(timezone.utc).timestamp()
        remaining_seconds = exp_ts - now_ts

        print(f"Expira em (UTC):  {exp_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        if remaining_seconds > 0:
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            print(f"Status: ATIVO (restam {minutes}m {seconds}s)")
        else:
            print("Status: EXPIRADO")

    print("=" * 70 + "\n")


def perform_login(username: str | None = None, password: str | None = None) -> None:
    """Perform login and save new token to .env."""
    if not username:
        username = os.environ.get("FAOSTAT_USERNAME") or input("Digite seu e-mail do FAOSTAT: ").strip()
    if not password:
        password = os.environ.get("FAOSTAT_PASSWORD") or getpass.getpass("Digite sua senha do FAOSTAT: ").strip()

    if not username or not password:
        print("Erro: Usuário e senha são obrigatórios.")
        return

    manager = FAOSTATAuthManager(username=username, password=password)
    try:
        token = manager.login(persist_to_env=True)
        print("\nSucesso! Novo FAOSTAT_TOKEN obtido e salvo no .env!")
        inspect_current_token()
    except Exception as exc:
        print(f"\nFalha na autenticação: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerenciador de Tokens FAOSTAT")
    parser.add_argument("--check", action="store_true", help="Inspeciona o token atual do .env")
    parser.add_argument("--login", action="store_true", help="Realiza login para gerar novo token")
    parser.add_argument("--username", type=str, help="E-mail de login no FAOSTAT")
    parser.add_argument("--password", type=str, help="Senha de login no FAOSTAT")

    args = parser.parse_args()

    if args.check:
        inspect_current_token()
    elif args.login or args.username or args.password:
        perform_login(args.username, args.password)
    else:
        # Default behavior: inspect, and if expired prompt to login
        inspect_current_token()
        manager = FAOSTATAuthManager()
        if not is_token_valid(manager.current_token):
            print("Deseja gerar um novo token agora programaticamente?")
            choice = input("Pressione 's' para fazer login ou qualquer outra tecla para sair: ").strip().lower()
            if choice == "s":
                perform_login()


if __name__ == "__main__":
    main()

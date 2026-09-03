"""Script utilitário para inicializar o front-end Streamlit do FertiPartner."""

import os
import sys
import subprocess
from pathlib import Path


def main() -> None:
    # Garante que a raiz do projeto e src/ estejam no PYTHONPATH
    root_dir = Path(__file__).resolve().parent.parent
    src_dir = root_dir / "src"
    app_file = src_dir / "app" / "presentation" / "streamlit" / "dashboard.py"

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(src_dir)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    print("==================================================================")
    print("Iniciando FertiPartner - Plataforma de Inteligencia NPK...")
    print(f"Arquivo Principal: {app_file}")
    print("==================================================================")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_file),
    ] + sys.argv[1:]

    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\nAplicação finalizada pelo usuário.")


if __name__ == "__main__":
    main()

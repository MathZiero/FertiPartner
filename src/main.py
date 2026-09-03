"""Ponto de entrada principal da aplicação FertiPartner."""

import sys
import subprocess
from pathlib import Path


def main() -> None:
    if "--dashboard" in sys.argv or "dashboard" in sys.argv:
        root_dir = Path(__file__).resolve().parent.parent
        dashboard_script = root_dir / "scripts" / "run_dashboard.py"
        subprocess.run([sys.executable, str(dashboard_script)] + [arg for arg in sys.argv[1:] if arg not in ("--dashboard", "dashboard")])
        return

    print("==================================================================")
    print("🌱 FertiPartner - Inteligência de Mercado de Fertilizantes (NPK)")
    print("==================================================================")
    print("Para iniciar a interface interativa em Streamlit + Plotly:")
    print("  uv run python scripts/run_dashboard.py")
    print("Ou execute:")
    print("  uv run python src/main.py --dashboard")
    print("==================================================================")


if __name__ == "__main__":
    main()

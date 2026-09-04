"""Ponto de entrada raiz da aplicação FertiPartner."""

import sys
import os
import subprocess
from pathlib import Path

# Configuração de encoding para evitar erros de charset no Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Garante que src/ esteja no sys.path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Detecta se está sendo executado através de 'streamlit run'
is_streamlit = False
try:
    import streamlit as st
    if st.runtime.exists():
        is_streamlit = True
except Exception:
    pass

if is_streamlit:
    # Execução direta via `streamlit run main.py`
    dashboard_path = src_dir / "app" / "presentation" / "streamlit" / "dashboard.py"
    with open(dashboard_path, "r", encoding="utf-8") as f:
        code = compile(f.read(), str(dashboard_path), "exec")
        exec_globals = globals()
        exec_globals["__file__"] = str(dashboard_path)
        exec(code, exec_globals)
else:
    def main() -> None:
        if "--dashboard" in sys.argv or "dashboard" in sys.argv:
            dashboard_script = root_dir / "scripts" / "run_dashboard.py"
            subprocess.run([sys.executable, str(dashboard_script)] + [arg for arg in sys.argv[1:] if arg not in ("--dashboard", "dashboard")])
            return

        print("==================================================================")
        print("🌱 FertiPartner - Inteligência de Mercado de Fertilizantes (NPK)")
        print("==================================================================")
        print("Para iniciar a interface interativa em Streamlit + Plotly:")
        print("  uv run python scripts/run_dashboard.py")
        print("Ou execute:")
        print("  uv run streamlit run main.py")
        print("  uv run python src/main.py --dashboard")
        print("==================================================================")

    if __name__ == "__main__":
        main()

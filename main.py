#!/usr/bin/env python
"""
KDP Discovery Engine Pro — Main Entry Point

Usage:
    streamlit run main.py                Launch interactive dashboard
    python main.py --cli <query>         Run CLI pipeline (headless)

Author: KDP Automation Architect
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: set project root as the working directory
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
os.chdir(str(ROOT))

# Ensure src/ is on the Python path so 'from core import ...' works
src_path = str(ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set default data and assets directories (can be overridden via config.ini)
os.environ.setdefault("KDP_DATA_DIR", str(ROOT / "data"))
os.environ.setdefault("KDP_ASSETS_DIR", str(ROOT / "assets"))

# ---------------------------------------------------------------------------
# CLI mode: python main.py --cli <query> [options]
# ---------------------------------------------------------------------------
if len(sys.argv) > 1 and sys.argv[1] == "--cli":
    sys.argv.pop(1)  # Remove --cli so cli.py gets the remaining args
    from src.cli import main as cli_main
    cli_main()
    sys.exit(0)

# ---------------------------------------------------------------------------
# Dashboard mode: streamlit run main.py
# ---------------------------------------------------------------------------
# Streamlit reads and executes this file. We redirect execution to
# src/dashboard.py which contains the full Streamlit app code.
_dashboard_path = ROOT / "src" / "dashboard.py"
if _dashboard_path.exists():
    with open(_dashboard_path, encoding="utf-8") as _f:
        exec(compile(_f.read(), _dashboard_path, "exec"))
else:
    print(f"FATAL: src/dashboard.py not found at {_dashboard_path}")
    sys.exit(1)

#!/usr/bin/env python
"""
PyArmor Obfuscation Script — KDP Discovery Engine Pro

Obfuscates the core analysis logic (EOS, UOI, profit algorithms)
to protect intellectual property from reverse engineering.

Prerequisites:
    pip install pyarmor

Usage:
    python pyarmor_build.py

Output:
    dist_obfuscated/
    ├── main.py              # Clean entry point
    ├── src/
    │   ├── dashboard.py     # Clean UI code
    │   ├── cli.py           # Clean CLI code
    │   └── core/
    │       ├── analyzer.py  # OBFUSCATED
    │       ├── database.py  # OBFUSCATED
    │       ├── scraper.py   # OBFUSCATED
    │       ├── exporter.py  # OBFUSCATED
    │       └── config_manager.py  # OBFUSCATED
    ├── config.ini
    ├── assets/
    ├── data/
    └── pyarmor/             # PyArmor runtime

After obfuscation, run PyInstaller to bundle into a single .exe:
    pyinstaller --clean build_spec.spec

Author: KDP Automation Architect
"""

import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
CORE_DIR = SRC_DIR / "core"
OUTPUT_DIR = PROJECT_ROOT / "dist_obfuscated"

# Files to obfuscate (core logic — IP protection)
FILES_TO_OBFUSCATE = [
    CORE_DIR / "analyzer.py",         # EOS, UOI, profit algorithms
    CORE_DIR / "database.py",         # DB schema and CRUD logic
    CORE_DIR / "scraper.py",          # API interaction logic
    CORE_DIR / "exporter.py",         # Export pipeline
    CORE_DIR / "config_manager.py",   # Config resolution chain
]

# Files to copy as-is (UI, entry points — no IP risk)
FILES_TO_COPY = [
    SRC_DIR / "dashboard.py",
    SRC_DIR / "cli.py",
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "config.ini",
]


def clean_output():
    """Remove previous obfuscation output."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def copy_directory_structure():
    """Replicate the project directory structure under output."""
    (OUTPUT_DIR / "src" / "core").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / ".streamlit").mkdir(parents=True, exist_ok=True)


def copy_assets():
    """Copy non-Python assets (config, icons, Streamlit settings)."""
    # .streamlit config
    src_config = PROJECT_ROOT / ".streamlit" / "config.toml"
    if src_config.exists():
        shutil.copy2(src_config, OUTPUT_DIR / ".streamlit" / "config.toml")

    # config.ini
    shutil.copy2(PROJECT_ROOT / "config.ini", OUTPUT_DIR / "config.ini")


def run_obfuscation():
    """Run PyArmor on core modules."""
    import pyarmor.pyarmor as pyarmor

    print("=" * 60)
    print("  PyArmor Obfuscation — KDP Discovery Engine Pro")
    print("=" * 60)

    obfuscate_cfg = {
        "input": str(CORE_DIR),
        "output": str(OUTPUT_DIR / "src" / "core"),
        "recursive": False,
        "exclude": "__init__.py",
        "obf_code": 2,           # Obfuscate bytecode (level 2)
        "obf_module": 1,         # Obfuscate module names
        "enable_jit": False,     # Disable JIT for compatibility
        "enable_snippet": False, # Keep full line numbers for debugging
        "restrict_mode": 0,      # No restrictions (PyInstaller compatible)
    }

    try:
        pyarmor.obfuscate(**obfuscate_cfg)
        print(f"  ✓ Core modules obfuscated to: {OUTPUT_DIR / 'src' / 'core'}")
    except Exception as e:
        print(f"  ✗ Obfuscation failed: {e}")
        print("  Falling back to copy (unobfuscated).")
        for f in FILES_TO_OBFUSCATE:
            shutil.copy2(f, OUTPUT_DIR / "src" / "core" / f.name)
        return False

    # Copy the PyArmor runtime key
    pyarmor_data = CORE_DIR / "pyarmor"
    if pyarmor_data.exists():
        shutil.copytree(pyarmor_data, OUTPUT_DIR / "src" / "core" / "pyarmor")

    return True


def copy_clean_files():
    """Copy non-obfuscated source files."""
    for f in FILES_TO_COPY:
        if f.exists():
            if f.parent == SRC_DIR:
                dest = OUTPUT_DIR / "src" / f.name
            else:
                dest = OUTPUT_DIR / f.name
            shutil.copy2(f, dest)
            print(f"  ✓ Copied: {f.name}")


def create_readme():
    """Create a README for the obfuscated distribution."""
    readme_content = """KDP Discovery Engine Pro — Obfuscated Distribution
====================================================================

This directory contains the obfuscated build of KDP Discovery Engine Pro.

The core analysis algorithms (analyzer.py, database.py, scraper.py,
exporter.py, config_manager.py) are protected with PyArmor bytecode
obfuscation to prevent reverse engineering.

Directory structure:
    main.py                 Entry point
    src/dashboard.py        Streamlit UI (clean)
    src/cli.py              CLI mode (clean)
    src/core/               Core modules (OBFUSCATED)
        analyzer.py
        database.py
        scraper.py
        exporter.py
        config_manager.py
    pyarmor/                PyArmor runtime (required)
    assets/                 Icons and resources
    config.ini              User configuration

Next step — build a single executable with PyInstaller:
    pip install pyinstaller
    pyinstaller --clean build_spec.spec

Or run directly (requires Python + dependencies):
    cd dist_obfuscated
    pip install streamlit pandas serpapi requests gspread google-auth
    streamlit run main.py
"""
    (OUTPUT_DIR / "README-OBFUSCATED.txt").write_text(readme_content, encoding="utf-8")
    print("  ✓ Created README-OBFUSCATED.txt")


def main():
    print()
    clean_output()
    copy_directory_structure()
    copy_assets()

    obfuscated = run_obfuscation()
    copy_clean_files()
    create_readme()

    print()
    print("-" * 60)
    if obfuscated:
        print("  Core modules are OBFUSCATED.")
    else:
        print("  WARNING: Core modules are NOT obfuscated (fallback copy used).")
    print(f"  Output: {OUTPUT_DIR}")
    print("-" * 60)
    print()
    print("Next step: pyinstaller --clean build_spec.spec")
    print()


if __name__ == "__main__":
    main()

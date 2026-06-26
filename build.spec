# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for KDP Research Pipeline Dashboard.

Packages app.py + core/ package into a single Windows executable.

Usage:
    pip install pyinstaller
    pyinstaller build.spec

Output: dist/KDP_Pipeline.exe
"""

import sys
from pathlib import Path

# -- Paths --------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_DIR = PROJECT_ROOT / "core"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

# -- Collect all Python files in core/ ---------------------------------------
# PyInstaller does not automatically detect imports inside packages,
# so we explicitly list every module in core/.
core_modules = sorted(str(p) for p in CORE_DIR.glob("*.py") if p.name != "__init__.py")

# -- Block any hidden imports for optional dependencies -----------------------
# gspread and google-auth are optional; if not installed, the exporter
# module degrades gracefully. We mark them as 'missing' so PyInstaller
# does not error when they are absent.

# -- Main block ---------------------------------------------------------------
a = Analysis(
    [str(PROJECT_ROOT / "app.py")] + core_modules,
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # Include .streamlit config folder for dark theme
        (str(PROJECT_ROOT / ".streamlit"), ".streamlit"),
        # Exclude .env (user provides own API key via Settings tab or .env)
    ],
    hiddenimports=[
        # Core package
        "core",
        "core.scraper",
        "core.analyzer",
        "core.exporter",
        "core.database",
        "core.config_manager",
        # serpapi is a compile-time import in core/scraper.py
        "serpapi",
        # pandas used by analyzer and app.py
        "pandas",
        # streamlit and its dependencies
        "streamlit",
        "streamlit.column_config",
        # gspread / google-auth — optional, suppress warnings
        "gspread",
        "google.oauth2",
        "google.oauth2.service_account",
    ],
    hookspath=[],
    hooksconfig={},
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "notebook",
        "jupyter",
        "ipython",
        "PIL",
        "cv2",
        "PyQt5",
        "sphinx",
        "unittest",
        "setuptools",
        "pip",
    ],
    runtime_hooks=[],
)

# -- Compress bytecode --------------------------------------------------------
pyz = PYZ(a.pure)

# -- Executable ---------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    # Metadata
    name="KDP_Pipeline",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                # no console window for end users
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon (optional — place an app.ico in project root)
    # icon=str(PROJECT_ROOT / "app.ico"),
)

# -- Also build the console variant for debugging / developer use -------------
exe_debug = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="KDP_Pipeline_DEBUG",
    debug=True,                   # verbose logging
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                 # show console window
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

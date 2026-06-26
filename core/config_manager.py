"""
config_manager.py -- User Configuration Persistence

Part of the KDP Research Pipeline core package.
Manages user-provided settings (SerpApi key, Sheet ID)
with a fallback chain: DB -> .env -> environment variable.

Author: KDP Automation Architect
"""

import os
import logging
from pathlib import Path
from typing import Optional

from . import database as db

logger = logging.getLogger("kdpconfig")

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DOTENV_PATH: Path = PROJECT_ROOT / ".env"


# ---------------------------------------------------------------------------
# SerpApi Key
# ---------------------------------------------------------------------------
def get_serpapi_key() -> str:
    """
    Resolve the SerpApi key using the priority chain:
        1. Database settings (set via Settings tab)
        2. .env file (legacy)
        3. SERPAPI_KEY environment variable
    """
    key = db.get_setting("serpapi_key")
    if key:
        return key
    key = _read_dotenv("SERPAPI_KEY")
    if key:
        return key
    return os.getenv("SERPAPI_KEY", "YOUR_SERPAPI_KEY_HERE")


def set_serpapi_key(key: str) -> bool:
    """Persist the SerpApi key to the database."""
    return db.set_setting("serpapi_key", key)


# ---------------------------------------------------------------------------
# Google Sheets ID
# ---------------------------------------------------------------------------
def get_sheet_id() -> str:
    """Resolve the Google Sheet ID: DB -> .env -> env var."""
    sid = db.get_setting("sheet_id")
    if sid:
        return sid
    sid = _read_dotenv("GOOGLE_SHEET_ID")
    if sid:
        return sid
    return os.getenv("GOOGLE_SHEET_ID", "")


def set_sheet_id(sheet_id: str) -> bool:
    """Persist the Sheet ID to the database."""
    return db.set_setting("sheet_id", sheet_id)


# ---------------------------------------------------------------------------
# Developer Mode (stored preference)
# ---------------------------------------------------------------------------
def get_dev_mode() -> bool:
    val = db.get_setting("dev_mode")
    if val is None:
        return False
    return val.lower() == "true"


def set_dev_mode(enabled: bool) -> bool:
    return db.set_setting("dev_mode", "true" if enabled else "false")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_dotenv(var_name: str) -> Optional[str]:
    """Read a variable from the .env file at project root."""
    try:
        if not DOTENV_PATH.exists():
            return None
        for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(var_name + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except Exception:
        pass
    return None

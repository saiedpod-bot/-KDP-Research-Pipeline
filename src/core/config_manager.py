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

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH: Path = PROJECT_ROOT / ".env"
CONFIG_INI_PATH: Path = PROJECT_ROOT / "config.ini"


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
# Generic key-value persistence (marketplace, profiles, etc.)
# ---------------------------------------------------------------------------
def get(key: str, default: str = "") -> str:
    """Resolve a generic setting: DB -> .env -> env var -> default."""
    val = db.get_setting(key)
    if val is not None:
        return val
    val = _read_dotenv(key.upper())
    if val:
        return val
    return os.getenv(key.upper(), default)


def set(key: str, value: str) -> bool:
    """Persist a generic setting to the database."""
    return db.set_setting(key, value)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_dotenv(var_name: str) -> Optional[str]:
    """Read a variable from .env or config.ini at project root.

    Priority: .env (legacy) > config.ini (preferred for distribution).
    """
    # Try .env first (legacy)
    val = _read_ini_file(DOTENV_PATH, var_name)
    if val:
        return val
    # Try config.ini (preferred in commercial distribution)
    val = _read_ini_file(CONFIG_INI_PATH, var_name)
    if val:
        return val
    return None


# ---------------------------------------------------------------------------
# Canva Integration Settings
# ---------------------------------------------------------------------------
def get_canva_template_url(book_type: str) -> str:
    """Get the Canva template URL for a given book type from config.ini.

    Parameters
    ----------
    book_type : str
        One of: 'Coloring Book', 'Planner', 'Activity Book'.
    """
    key_map = {
        "Coloring Book": "COLORING_TEMPLATE",
        "Planner": "PLANNER_TEMPLATE",
        "Activity Book": "ACTIVITY_TEMPLATE",
    }
    key = key_map.get(book_type)
    if not key:
        return ""
    return _read_ini_section_key("Canva", key)


def get_canva_client_id() -> str:
    return _read_ini_section_key("Canva", "CANVA_CLIENT_ID") or os.getenv("CANVA_CLIENT_ID", "")


def get_canva_client_secret() -> str:
    return _read_ini_section_key("Canva", "CANVA_CLIENT_SECRET") or os.getenv("CANVA_CLIENT_SECRET", "")


def _read_ini_section_key(section: str, key: str) -> str:
    """Read a specific key from a [section] in config.ini."""
    path = CONFIG_INI_PATH
    if not path.exists():
        return ""
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped[1:-1].strip() == section
            continue
        if not in_section:
            continue
        if "=" not in stripped:
            continue
        k, _, v = stripped.partition("=")
        if k.strip().upper() == key.upper():
            return v.strip().strip("\"'")
    return ""


def _read_ini_file(path: Path, var_name: str) -> Optional[str]:
    """Read a KEY=VALUE pair from a simple ini-style file."""
    try:
        if not path.exists():
            return None
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            # Skip sections [section] and comments
            if not line or line.startswith("[") or line.startswith("#") or line.startswith(";"):
                continue
            if line.startswith(var_name + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    except Exception:
        pass
    return None

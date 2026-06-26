"""
database.py -- SQLite Storage for Search History & Settings

Part of the KDP Research Pipeline core package.
Provides persistent storage across sessions:
  - search_history: query, parameters, timestamp, results JSON
  - settings: key/value config (SerpApi key, Sheet ID, etc.)

Author: KDP Automation Architect
"""

import os
import json
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("kdpdb")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DB_DIR: Path = PROJECT_ROOT / "database"
DB_PATH: Path = DB_DIR / "kdp_history.db"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Open (and create if needed) the SQLite database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every startup."""
    try:
        conn = get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS search_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                query           TEXT    NOT NULL,
                max_pages       INTEGER DEFAULT 3,
                min_price       REAL    DEFAULT 7.00,
                sheet_id        TEXT    DEFAULT '',
                product_count   INTEGER DEFAULT 0,
                opportunity_count INTEGER DEFAULT 0,
                gem_count       INTEGER DEFAULT 0,
                results_json    TEXT    DEFAULT '[]',
                created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS discovery_queue (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_query    TEXT    NOT NULL,
                term            TEXT    NOT NULL,
                source          TEXT    DEFAULT 'category',
                origin_asin     TEXT    DEFAULT '',
                score           INTEGER DEFAULT 50,
                searched        INTEGER DEFAULT 0,
                created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS discovered_niches (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_query    TEXT    NOT NULL,
                term            TEXT    NOT NULL,
                source          TEXT    DEFAULT 'auto',
                connection_score INTEGER DEFAULT 0,
                product_count   INTEGER DEFAULT 0,
                opportunity_count INTEGER DEFAULT 0,
                avg_price       REAL    DEFAULT 0.0,
                searched_at     TEXT    DEFAULT (datetime('now', 'localtime'))
            );
        """)
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc)


# ---------------------------------------------------------------------------
# Search History
# ---------------------------------------------------------------------------
def save_search(
    query: str,
    max_pages: int = 3,
    min_price: float = 7.00,
    sheet_id: Optional[str] = None,
    results: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Persist a completed search to the history table.

    Returns the new row id, or None on failure.
    """
    try:
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO search_history
                (query, max_pages, min_price, sheet_id,
                 product_count, opportunity_count, gem_count, results_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                query,
                max_pages,
                min_price,
                sheet_id or "",
                (results or {}).get("scraped_count", 0),
                (results or {}).get("opportunity_count", 0),
                (results or {}).get("gem_count", 0),
                json.dumps((results or {}).get("ranked_rows", []), ensure_ascii=False),
            ),
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        logger.info("Saved search #%d to history: '%s'", row_id, query)
        return row_id
    except Exception as exc:
        logger.error("Failed to save search history: %s", exc)
        return None


def get_history(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Return recent searches (most recent first).
    Each row contains metadata but NOT the full results JSON.
    """
    try:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT id, query, max_pages, min_price, sheet_id,
                   product_count, opportunity_count, gem_count, created_at
            FROM search_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch search history: %s", exc)
        return []


def get_search_by_id(search_id: int) -> Optional[Dict[str, Any]]:
    """
    Load a full search result by its id, including the ranked_rows JSON.
    Returns None if not found.
    """
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM search_history WHERE id = ?", (search_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        result = dict(row)
        result["ranked_rows"] = json.loads(result.pop("results_json", "[]"))
        return result
    except Exception as exc:
        logger.error("Failed to load search #%d: %s", search_id, exc)
        return None


def delete_search(search_id: int) -> bool:
    """Remove a search history entry by id."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM search_history WHERE id = ?", (search_id,))
        conn.commit()
        conn.close()
        logger.info("Deleted search #%d from history.", search_id)
        return True
    except Exception as exc:
        logger.error("Failed to delete search #%d: %s", search_id, exc)
        return False


# ---------------------------------------------------------------------------
# Settings (key/value store)
# ---------------------------------------------------------------------------
def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a setting value by key."""
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception as exc:
        logger.error("Failed to read setting '%s': %s", key, exc)
        return default


def set_setting(key: str, value: str) -> bool:
    """Persist a setting (upsert by key)."""
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        conn.commit()
        conn.close()
        logger.debug("Setting '%s' updated.", key)
        return True
    except Exception as exc:
        logger.error("Failed to save setting '%s': %s", key, exc)
        return False


# ---------------------------------------------------------------------------
# Discovery Queue
# ---------------------------------------------------------------------------
def save_discovery_terms(
    origin_query: str,
    terms: List[Dict[str, Any]],
) -> int:
    """Insert a batch of discovery terms into the queue. Returns count inserted."""
    count = 0
    try:
        conn = get_connection()
        for term in terms:
            t = term.get("term", "").strip()
            if not t:
                continue
            # Avoid inserting exact duplicates for the same origin_query
            existing = conn.execute(
                "SELECT id FROM discovery_queue WHERE origin_query = ? AND term = ?",
                (origin_query, t),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """INSERT INTO discovery_queue
                   (origin_query, term, source, origin_asin, score)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    origin_query,
                    t,
                    term.get("source", "category"),
                    term.get("origin_asin", ""),
                    term.get("score", 50),
                ),
            )
            count += 1
        conn.commit()
        conn.close()
        if count:
            logger.info("Discovery queue: added %d terms from '%s'", count, origin_query)
        return count
    except Exception as exc:
        logger.error("Failed to save discovery terms: %s", exc)
        return 0


def get_discovery_queue(
    searched: Optional[bool] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """Return discovery queue entries, optionally filtered by search state."""
    try:
        conn = get_connection()
        if searched is not None:
            flag = 1 if searched else 0
            rows = conn.execute(
                """SELECT * FROM discovery_queue
                   WHERE searched = ?
                   ORDER BY score DESC, created_at DESC
                   LIMIT ?""",
                (flag, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM discovery_queue
                   ORDER BY score DESC, created_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch discovery queue: %s", exc)
        return []


def mark_discovery_searched(entry_id: int) -> bool:
    """Mark a single queue entry as searched."""
    try:
        conn = get_connection()
        conn.execute("UPDATE discovery_queue SET searched = 1 WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        logger.error("Failed to mark discovery #%d as searched: %s", entry_id, exc)
        return False


def clear_discovery_queue() -> bool:
    """Remove all entries from the discovery queue."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM discovery_queue")
        conn.commit()
        conn.close()
        logger.info("Discovery queue cleared.")
        return True
    except Exception as exc:
        logger.error("Failed to clear discovery queue: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Discovered Niches (results of secondary scans)
# ---------------------------------------------------------------------------
def save_discovered_niche(
    origin_query: str,
    term: str,
    source: str = "auto",
    connection_score: int = 0,
    product_count: int = 0,
    opportunity_count: int = 0,
    avg_price: float = 0.0,
) -> Optional[int]:
    """Persist a discovered-niche result. Returns row id or None."""
    try:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO discovered_niches
               (origin_query, term, source, connection_score,
                product_count, opportunity_count, avg_price)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (origin_query, term, source, connection_score,
             product_count, opportunity_count, avg_price),
        )
        row_id = cur.lastrowid
        conn.commit()
        conn.close()
        return row_id
    except Exception as exc:
        logger.error("Failed to save discovered niche: %s", exc)
        return None


def get_discovered_niches(limit: int = 50) -> List[Dict[str, Any]]:
    """Return all discovered niches, highest score first."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM discovered_niches
               ORDER BY connection_score DESC, searched_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch discovered niches: %s", exc)
        return []


def delete_discovered_niche(niche_id: int) -> bool:
    """Remove a discovered niche by id."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM discovered_niches WHERE id = ?", (niche_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        logger.error("Failed to delete niche #%d: %s", niche_id, exc)
        return False

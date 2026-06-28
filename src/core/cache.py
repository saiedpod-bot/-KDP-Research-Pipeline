"""
cache.py — Local JSON cache for provider scrape results.

Usage::

    from core.cache import get_or_scrape

    data = get_or_scrape("coloring book adults", "oxylabs", lambda: provider.scrape(...))

Cache files are stored under ``project_root / cache / {query_hash}.json``.
The hash is derived from ``(query + provider_slug)`` so the same query
with different providers is cached separately.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("kdp.cache")

# Project root (parent of src/core)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CACHE_DIR = _PROJECT_ROOT / "cache"


def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _query_hash(query: str, provider_slug: str) -> str:
    raw = f"{query.strip().lower()}|{provider_slug.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_cached(query: str, provider_slug: str) -> Optional[Dict[str, Any]]:
    """Return cached result for *(query, provider)* or ``None``."""
    h = _query_hash(query, provider_slug)
    path = _CACHE_DIR / f"{h}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Cache HIT for '%s' (provider=%s, hash=%s)", query, provider_slug, h)
        return data
    except Exception as exc:
        logger.warning("Cache read error for %s: %s", path, exc)
        return None


def set_cached(query: str, provider_slug: str, data: Dict[str, Any]) -> None:
    """Persist *data* to cache under *(query, provider)*."""
    _ensure_cache_dir()
    h = _query_hash(query, provider_slug)
    path = _CACHE_DIR / f"{h}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Cache SAVE for '%s' (provider=%s, hash=%s)", query, provider_slug, h)
    except Exception as exc:
        logger.warning("Cache write error for %s: %s", path, exc)


def clear_cache() -> int:
    """Remove all cache files. Returns the number of files deleted."""
    _ensure_cache_dir()
    count = 0
    for p in _CACHE_DIR.iterdir():
        if p.suffix == ".json":
            try:
                p.unlink()
                count += 1
            except Exception:
                pass
    logger.info("Cache cleared — %d files removed.", count)
    return count


def get_or_scrape(
    query: str,
    provider_slug: str,
    scrape_fn: Callable[[], Optional[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """
    Return cached data if available, otherwise call *scrape_fn*, cache the
    result, and return it.

    Parameters
    ----------
    query : str
        Search keyword (used for cache key).
    provider_slug : str
        Provider identifier (e.g. ``"pangolinfo"``, ``"oxylabs"``).
    scrape_fn : callable
        Zero-argument callable that performs the actual scrape and returns
        a dict (or ``None`` on failure).

    Returns
    -------
    dict or None
    """
    cached = get_cached(query, provider_slug)
    if cached is not None:
        return cached

    data = scrape_fn()
    if data is not None and "error" not in data:
        set_cached(query, provider_slug, data)
    return data

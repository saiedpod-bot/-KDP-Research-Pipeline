"""
pre_research.py — Zero-credit keyword discovery via free public APIs

Provides Google Suggest-based keyword expansion so the user can explore
niche ideas **before** spending a Pangolinfo credit.
"""

import logging
from typing import Dict, List, Any

import requests

logger = logging.getLogger("kdppreresearch")

GOOGLE_SUGGEST_URL = "https://suggestqueries.google.com/complete/search"

COMMON_KDP_NICHES: List[str] = [
    "coloring book",
    "activity book",
    "planner",
    "journal",
    "sketch book",
    "workbook",
    "log book",
    "composition book",
    "notebook",
    "dot grid",
    "guest book",
    "recipe book",
    "budget planner",
    "meal planner",
    "gratitude journal",
    "baby book",
    "travel journal",
    "mazes",
    "dot to dot",
    "how to draw",
    "story paper",
    "handwriting practice",
    "sight words",
    "math workbook",
    "tracing book",
    "word search",
    "crossword",
    "sudoku",
    "cryptogram",
    "trivia book",
]

# Prefixes to feed to Google Suggest for deeper expansion
_EXPANSION_PREFIXES = [
    "coloring book for",
    "activity book for",
    "planner for",
    "journal for",
    "workbook for",
    "how to draw",
    "mazes for",
    "word search for",
]


def google_suggest(keyword: str, max_results: int = 10) -> List[str]:
    """
    Fetch keyword suggestions from Google Suggest (zero cost).

    Parameters
    ----------
    keyword : str
        The search term to expand.
    max_results : int, optional
        Max suggestions to return (default 10).

    Returns
    -------
    list[str]
        Suggested keywords, or empty list on failure.
    """
    try:
        resp = requests.get(
            GOOGLE_SUGGEST_URL,
            params={"client": "firefox", "q": keyword},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning("Google Suggest returned HTTP %d", resp.status_code)
            return []
        data = resp.json()
        suggestions = data[1] if isinstance(data, list) and len(data) > 1 else []
        return [str(s) for s in suggestions[:max_results]]
    except Exception as exc:
        logger.warning("Google Suggest failed for '%s': %s", keyword, exc)
        return []


def expand_keywords(broad_term: str) -> List[Dict[str, Any]]:
    """
    Generate a list of niche keyword ideas from a broad term using Google Suggest.

    This is the primary entry point for the pre-research tier. It:
      1. Calls Google Suggest with the raw term.
      2. Also queries known expansion prefixes if the term matches them.
      3. Deduplicates and returns all results with metadata.

    Parameters
    ----------
    broad_term : str
        A broad category or idea (e.g. "coloring book").

    Returns
    -------
    list[dict]
        Each item: {"keyword": str, "source": str, "suggested": str}
    """
    seen: set = set()
    results: List[Dict[str, Any]] = []
    lower = broad_term.lower().strip()

    def _add(kw: str, src: str) -> None:
        key = kw.lower().strip()
        if key and key not in seen:
            seen.add(key)
            results.append({"keyword": kw.strip(), "source": src})

    # 1. Direct Google Suggest
    direct = google_suggest(broad_term)
    for s in direct:
        _add(s, "google_suggest")

    # 2. If the term matches a known prefix, expand further
    prefixes_to_try = []
    for prefix in _EXPANSION_PREFIXES:
        if prefix.startswith(lower):
            prefixes_to_try.append(prefix)
    # Also try general: append common suffixes
    for suffix in ["for adults", "for kids", "for beginners", "ideas", "printable", "bulk"]:
        test = f"{broad_term} {suffix}"
        expanded = google_suggest(test)
        for s in expanded:
            _add(s, f"google_suggest+{suffix}")

    # 3. For each prefix that matches, get its suggestions
    for prefix in prefixes_to_try:
        expanded = google_suggest(prefix)
        for s in expanded:
            _add(s, "google_suggest_prefix")

    # 4. Fallback: if results are empty, seed with common niche prefixes
    if not results:
        for prefix in _EXPANSION_PREFIXES[:6]:
            expanded = google_suggest(prefix)
            for s in expanded:
                _add(s, "google_suggest_fallback")

    return results


def get_niche_suggestions(broad_term: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    High-level API: returns ranked niche keyword suggestions with metadata.

    Parameters
    ----------
    broad_term : str
        Broad input (e.g. "coloring book").
    max_results : int, optional
        Max items to return (default 20).

    Returns
    -------
    list[dict]
        Sorted list of suggestion dicts.
    """
    ideas = expand_keywords(broad_term)

    # Remove exact match to "keyword" itself
    lower = broad_term.lower().strip()
    ideas = [i for i in ideas if i["keyword"].lower().strip() != lower]

    # Sort: prefer shorter suggestions first (more generic = broader reach)
    ideas.sort(key=lambda x: len(x["keyword"]))

    return ideas[:max_results]

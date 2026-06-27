"""
scraper.py — Tier 1: Data Gathering Module

Part of the Amazon KDP Research Pipeline.
Uses SerpApi to search Amazon and return structured product data.
Additive-only module: extend with new functions/classes, never rewrite existing.

Output Schema:
    [ASIN, Title, Author, Price, BSR, ReviewCount, Rating, PublicationDate]

Dependencies:
    pip install requests serpapi

Author: KDP Automation Architect
"""

import os
import sys
import re
import json
import time
import logging
from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime
from pathlib import Path

from serpapi import Client, SerpResults


# ---------------------------------------------------------------------------
# .env / config.ini loader — keeps API keys out of version control
# Looks in project root (three levels up from src/core/scraper.py).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
for _cfg_file in (_PROJECT_ROOT / "config.ini", _ENV_PATH):
    if _cfg_file.exists():
        with open(_cfg_file, encoding="utf-8") as _fh:
            for _line in _fh:
                _line = _line.strip()
                if _line and not _line.startswith("#") and not _line.startswith("[") and not _line.startswith(";") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
        break  # prefer config.ini over .env


# ---------------------------------------------------------------------------
# Logging setup — consistent across all pipeline modules
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_PROJECT_ROOT / "data" / "scraper.log", mode="a"),
    ],
)
logger = logging.getLogger("kdpscraper")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Reads from .env → env var → fallback placeholder.
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "YOUR_SERPAPI_KEY_HERE")

# Pangolinfo Amazon Scrape API token
PANGOLINFO_TOKEN: str = os.getenv("PANGOLINFO_TOKEN", "")
PANGOLINFO_API_URL: str = "https://scrapeapi.pangolinfo.com/api/v1/scrape"

# Amazon marketplace domain — change per target region
AMAZON_DOMAIN: str = "amazon.com"

# Delay (seconds) between consecutive API calls to avoid rate limits
REQUEST_DELAY: float = 2.0

# Output directory — relative to project root so scraper + analyzer share the same path
OUTPUT_DIR: str = "output"

# Absolute path to the project root (parent of src/) for cross-module file consistency
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Core: Fetch Amazon search results via SerpApi
# ---------------------------------------------------------------------------
def fetch_amazon_data(
    query: str,
    api_key: str,
    domain: str = AMAZON_DOMAIN,
    max_retries: int = 3,
    filter_params: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Search Amazon via SerpApi and return the raw JSON response.

    Parameters
    ----------
    query : str
        Search term (e.g. "low fodmap cookbook for kids").
    api_key : str
        Valid SerpApi key.
    domain : str
        Amazon marketplace domain (default: amazon.com).
    max_retries : int
        Number of retry attempts on failure.
    filter_params : dict, optional
        Additional Amazon search parameters (e.g. ``rh`` for refinement).
        Passed directly to SerpApi.

    Returns
    -------
    dict or None
        Raw SerpApi response JSON, or None if all retries fail.
    """
    params: Dict[str, Any] = {
        "engine": "amazon",
        "amazon_domain": domain,
        "k": query,
        "gl": "us",
        "hl": "en-us",
    }
    if filter_params:
        params.update(filter_params)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Searching Amazon for: '%s' (attempt %d/%d)",
                query, attempt, max_retries,
            )
            client = Client(api_key=api_key)
            raw: SerpResults = client.search(**params)

            # SerpApi returns an "error" key on failure
            if "error" in raw:
                logger.error("SerpApi returned an error: %s", raw["error"])
                return None

            logger.info(
                "Success — found %d organic results for '%s'",
                len(raw.get("organic_results", [])),
                query,
            )
            return dict(raw)  # convert UserDict to plain dict

        except Exception as exc:
            logger.warning("Attempt %d/%d failed: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                wait = REQUEST_DELAY * (2 ** (attempt - 1))  # exponential back-off
                logger.info("Waiting %.1f seconds before retry…", wait)
                time.sleep(wait)
            else:
                logger.error("All %d attempts exhausted for query '%s'.", max_retries, query)
                return None


# ---------------------------------------------------------------------------
# Helper: extract the author from a SerpApi result item
# ---------------------------------------------------------------------------
def _extract_author(item: Dict[str, Any]) -> str:
    """
    Best-effort extraction of the author / brand name.

    Priority order:
      1. `seller_name` field (SerpApi often puts the author here for books)
      2. `brand` field
      3. "Unknown" fallback
    """
    try:
        author: Optional[str] = item.get("seller_name") or item.get("brand")
        return str(author).strip() if author else "Unknown"
    except Exception:
        return "Unknown"


# ---------------------------------------------------------------------------
# Helper: extract publication date from SerpApi item
# ---------------------------------------------------------------------------
def _extract_publication_date(item: Dict[str, Any]) -> str:
    """
    Best-effort extraction of the publication date.

    Tries, in order:
      1. `publication_date` field
      2. `extensions.publication_date` nested field
      3. "N/A" fallback
    """
    try:
        pub = item.get("publication_date")
        if pub:
            return str(pub)
        ext = item.get("extensions") or {}
        if isinstance(ext, dict):
            pub = ext.get("publication_date")
            if pub:
                return str(pub)
        return "N/A"
    except Exception:
        return "N/A"


# ---------------------------------------------------------------------------
# Helper: parse price string to float
# ---------------------------------------------------------------------------
def _parse_price(item: Dict[str, Any]) -> float:
    """
    Return the listing price as a float, or 0.0 if parsing fails.
    """
    try:
        # SerpApi usually provides an `extracted_price` key
        price = item.get("extracted_price")
        if price is not None:
            return float(price)

        # Fallback: try parsing the string price field
        price_str: str = item.get("price", "$0.00")
        cleaned: str = price_str.replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Helper: parse review count
# ---------------------------------------------------------------------------
def _parse_review_count(item: Dict[str, Any]) -> int:
    """
    Return the total number of reviews, or 0 if unavailable.
    """
    try:
        count = item.get("ratings_total")
        return int(count) if count is not None else 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Helper: parse star rating
# ---------------------------------------------------------------------------
def _parse_rating(item: Dict[str, Any]) -> float:
    """
    Return the star rating (0.0 – 5.0), or 0.0 if unavailable.
    """
    try:
        rating = item.get("rating")
        return float(rating) if rating is not None else 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Transform: raw SerpApi response → unified list of dicts matching the schema
# ---------------------------------------------------------------------------
def format_data_for_csv(raw_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract structured product data from the raw SerpApi JSON.

    Returns a list of dicts, each conforming to:
        [ASIN, Title, Author, Price, BSR, ReviewCount, Rating, PublicationDate]

    Notes
    -----
    - BSR and PublicationDate are not available from SerpApi search results.
      They require a product-detail scrape (future Tier expansion).
      Here they are set to 0 / "N/A" as placeholders.
    """
    rows: List[Dict[str, Any]] = []

    try:
        results: List[Dict[str, Any]] = raw_json.get("organic_results", [])
        if not results:
            logger.warning("No organic results found in the response.")
            return rows

        for position, item in enumerate(results, start=1):
            try:
                row = {
                    "ASIN": item.get("asin", "N/A"),
                    "Title": item.get("title", "").strip(),
                    "Author": _extract_author(item),
                    "Price": _parse_price(item),
                    "BSR": 0,                 # requires product-detail endpoint
                    "ReviewCount": _parse_review_count(item),
                    "Rating": _parse_rating(item),
                    "PublicationDate": _extract_publication_date(item),
                    "Position": position,
                    "thumbnail": item.get("thumbnail", ""),
                }
                rows.append(row)
            except Exception as exc:
                # Log a single bad item but continue processing the rest
                asin = item.get("asin", "UNKNOWN")
                logger.warning("Skipping item %s due to parsing error: %s", asin, exc)
                continue

        logger.info("Formatted %d / %d results into schema rows.", len(rows), len(results))
        return rows

    except Exception as exc:
        logger.error("Failed to process raw JSON: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Saver: write raw JSON + formatted CSV to disk
# ---------------------------------------------------------------------------
def save_results(
    query: str,
    raw_json: Dict[str, Any],
    formatted_rows: List[Dict[str, Any]],
) -> None:
    """
    Persist both the raw API response (as JSON) and the formatted rows (as JSON)
    to the output directory. A CSV writer will be added in Tier 3.

    Uses PROJECT_ROOT as the base path so analyzer.py can find the same files.
    """
    try:
        out_dir = PROJECT_ROOT / OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        safe_name: str = query.lower().replace(" ", "_")[:60]

        # Raw dump
        raw_path = out_dir / f"raw_{safe_name}.json"
        with open(raw_path, "w", encoding="utf-8") as fh:
            json.dump(raw_json, fh, indent=2, ensure_ascii=False)
        logger.info("Raw response saved -> %s", raw_path)

        # Formatted dump
        fmt_path = out_dir / f"formatted_{safe_name}.json"
        with open(fmt_path, "w", encoding="utf-8") as fh:
            json.dump(formatted_rows, fh, indent=2, ensure_ascii=False)
        logger.info("Formatted rows saved -> %s", fmt_path)

    except Exception as exc:
        logger.error("Failed to save results to disk: %s", exc)


# ---------------------------------------------------------------------------
# Pagination: fetch multiple pages using the 'start' offset parameter
# ---------------------------------------------------------------------------
def fetch_all_pages(
    query: str,
    max_pages: int = 5,
    api_key: str = SERPAPI_KEY,
    domain: str = AMAZON_DOMAIN,
    page_size: int = 20,
    filter_params: Optional[Dict[str, str]] = None,
    progress_callback: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch multiple pages of Amazon search results using the SerpApi
    ``start`` offset parameter.

    Each page fetches up to *page_size* results.  With the default
    *max_pages=5* and *page_size=20* you can expect **~80-100+** products.

    Parameters
    ----------
    query : str
        Amazon search term.
    max_pages : int
        Number of result pages to fetch (default: 5).
    api_key : str
        Valid SerpApi key.
    domain : str
        Amazon marketplace domain (default: amazon.com).
    page_size : int
        Results offset increment between pages (default: 20).
    filter_params : dict, optional
        Additional Amazon search parameters (e.g. ``rh`` for refinement).
    progress_callback : callable, optional
        Called as progress_callback(current_page, max_pages) after each page.

    Returns
    -------
    list[dict]
        Formatted product rows (one dict per product, deduplicated by ASIN).
        Empty list if all requests fail.
    """
    all_items: List[Dict[str, Any]] = []
    seen_asins: set = set()

    client = Client(api_key=api_key)

    for page in range(1, max_pages + 1):
        start_offset = (page - 1) * page_size
        params: Dict[str, Any] = {
            "engine": "amazon",
            "amazon_domain": domain,
            "k": query,
            "gl": "us",
            "hl": "en-us",
            "start": start_offset,
        }
        if filter_params:
            params.update(filter_params)

        for attempt in range(1, 4):
            try:
                logger.info(
                    "Page %d/%d (start=%d) ...",
                    page, max_pages, start_offset,
                )
                raw = client.search(**params)

                if "error" in raw:
                    logger.error(
                        "Page %d — error: %s", page, raw["error"],
                    )
                    break

                organic = raw.get("organic_results", [])
                logger.info(
                    "Page %d — %d items received.", page, len(organic),
                )

                # Stop if page is empty (no more results available)
                if not organic:
                    logger.info(
                        "Page %d returned 0 items — no more results. Stopping.",
                        page,
                    )
                    break

                # Deduplicate and collect
                page_new = 0
                for item in organic:
                    asin = item.get("asin")
                    if asin and asin not in seen_asins:
                        seen_asins.add(asin)
                        all_items.append(item)
                        page_new += 1
                logger.info(
                    "Page %d — %d new (deduped).", page, page_new,
                )

                if progress_callback:
                    progress_callback(page, max_pages)

                # Respect rate limits — 2-second gap between pages
                if page < max_pages:
                    time.sleep(REQUEST_DELAY)

                break  # success

            except Exception as exc:
                logger.warning(
                    "Page %d, attempt %d/3 failed: %s",
                    page, attempt, exc,
                )
                if attempt < 3:
                    time.sleep(REQUEST_DELAY * (2 ** (attempt - 1)))

    logger.info(
        "Fetch-all complete — %d pages, %d unique products.",
        max_pages, len(all_items),
    )

    # Format raw items into schema rows
    rows: List[Dict[str, Any]] = []
    for position, item in enumerate(all_items, start=1):
        try:
            rows.append({
                "ASIN": item.get("asin", "N/A"),
                "Title": (item.get("title") or "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": _extract_publication_date(item),
                "Position": position,
                "thumbnail": item.get("thumbnail", ""),
            })
        except Exception as exc:
            logger.warning(
                "Skipping item %s: %s",
                item.get("asin", "?"), exc,
            )

    logger.info("Formatted %d schema rows.", len(rows))
    return rows


# ---------------------------------------------------------------------------
# Pagination: fetch multiple pages for 100+ results  (yield_pages variant)
# ---------------------------------------------------------------------------
def fetch_amazon_data_paginated(
    query: str,
    api_key: str,
    domain: str = AMAZON_DOMAIN,
    max_pages: int = 5,
    page_delay: float = 2.0,
    filter_params: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch multiple pages of Amazon search results via SerpApi.

    Each page typically yields 10-20 organic results.  With the default
    5 pages you can expect **~75-100+** product entries.

    Uses SerpResults' built-in ``yield_pages()`` iterator for clean
    multi-page traversal with automatic pagination-link following.

    Parameters
    ----------
    query : str
        Search term.
    api_key : str
        Valid SerpApi key.
    domain : str
        Amazon marketplace domain (default: amazon.com).
    max_pages : int
        Number of result pages to fetch (default: 5).
    page_delay : float
        Seconds to wait between page requests (default: 2.0).
    filter_params : dict, optional
        Additional Amazon search parameters (e.g. ``rh`` for refinement).

    Returns
    -------
    list[dict]
        Raw SerpApi response dict for **each** successfully fetched page.
        An empty list means all requests failed.
    """
    raw_responses: List[Dict[str, Any]] = []

    params: Dict[str, Any] = {
        "engine": "amazon",
        "amazon_domain": domain,
        "k": query,
        "gl": "us",
        "hl": "en-us",
    }
    if filter_params:
        params.update(filter_params)

    client = Client(api_key=api_key)

    for attempt in range(1, 4):  # 3 retries for initial request
        try:
            logger.info("Fetching page 1/%d for '%s' …", max_pages, query)
            first_page: SerpResults = client.search(**params)

            if "error" in first_page:
                logger.error("SerpApi error: %s", first_page["error"])
                return []

            raw_responses.append(dict(first_page))
            logger.info(
                "Page 1 — %d organic results.",
                len(first_page.get("organic_results", [])),
            )
            break  # initial request succeeded
        except Exception as exc:
            logger.warning(
                "Initial request, attempt %d/3 failed: %s", attempt, exc,
            )
            if attempt < 3:
                time.sleep(REQUEST_DELAY * (2 ** (attempt - 1)))
            else:
                logger.error("Giving up on initial request after 3 attempts.")
                return []

    # Pages 2+ via yield_pages
    page_count = 1
    try:
        for next_page in first_page.yield_pages(max_pages):
            page_count += 1
            if page_count > max_pages:
                break
            logger.info("Fetching page %d/%d …", page_count, max_pages)

            if "error" in next_page:
                logger.error(
                    "Page %d — SerpApi error: %s",
                    page_count, next_page["error"],
                )
                break

            raw_responses.append(dict(next_page))
            logger.info(
                "Page %d — %d organic results.",
                page_count,
                len(next_page.get("organic_results", [])),
            )

            if page_count < max_pages:
                time.sleep(page_delay)

    except Exception as exc:
        logger.warning(
            "Pagination stopped at page %d: %s", page_count, exc,
        )

    logger.info(
        "Paginated fetch complete — %d pages, %d raw responses.",
        page_count,
        len(raw_responses),
    )
    return raw_responses


def merge_organic_results(
    raw_responses: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Merge organic results from multiple SerpApi page responses and
    deduplicate by ASIN.

    Parameters
    ----------
    raw_responses : list[dict]
        Raw JSON responses from ``fetch_amazon_data_paginated``.

    Returns
    -------
    list[dict]
        Deduplicated list of organic-result items.
    """
    seen: set = set()
    merged: List[Dict[str, Any]] = []

    for resp in raw_responses:
        for item in resp.get("organic_results", []):
            asin = item.get("asin")
            if asin and asin not in seen:
                seen.add(asin)
                merged.append(item)

    logger.info(
        "Merged %d raw responses into %d unique organic results.",
        len(raw_responses),
        len(merged),
    )
    return merged


def search_and_format_batch(
    query: str,
    api_key: str = SERPAPI_KEY,
    domain: str = AMAZON_DOMAIN,
    max_pages: int = 5,
    save: bool = True,
    filter_params: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    High-level wrapper for batch (paginated) scraping.

    1. Fetch *max_pages* pages of Amazon search results.
    2. Deduplicate organic results by ASIN.
    3. Format each result into the unified schema row.
    4. Optionally save raw + formatted data to disk.

    Parameters
    ----------
    query : str
        Amazon search term.
    api_key : str
        SerpApi key.
    domain : str
        Amazon marketplace domain.
    max_pages : int
        Number of pages to fetch (default: 5).
    save : bool
        If True, write raw + formatted JSON to disk.
    filter_params : dict, optional
        Additional Amazon search parameters (e.g. ``rh`` for refinement).

    Returns
    -------
    list[dict]
        Deduplicated, formatted product rows.
    """
    raw_responses = fetch_amazon_data_paginated(
        query=query,
        api_key=api_key,
        domain=domain,
        max_pages=max_pages,
        filter_params=filter_params,
    )
    if not raw_responses:
        logger.error("Batch fetch returned 0 pages for '%s'.", query)
        return []

    merged_items = merge_organic_results(raw_responses)

    rows: List[Dict[str, Any]] = []
    for position, item in enumerate(merged_items, start=1):
        try:
            row = {
                "ASIN": item.get("asin", "N/A"),
                "Title": item.get("title", "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": _extract_publication_date(item),
                "Position": position,
                "thumbnail": item.get("thumbnail", ""),
            }
            rows.append(row)
        except Exception as exc:
            asin = item.get("asin", "UNKNOWN")
            logger.warning("Skipping item %s: %s", asin, exc)

    logger.info(
        "Formatted %d / %d merged items into schema rows.",
        len(rows),
        len(merged_items),
    )

    if save:
        # For the raw save, build a synthetic combined JSON
        combined_raw = {
            "query": query,
            "total_pages": len(raw_responses),
            "total_organic_results": len(merged_items),
            "organic_results": merged_items,
        }
        save_results(query, combined_raw, rows)

    return rows


# ---------------------------------------------------------------------------
# Convenience: run a full search-and-format cycle
# ---------------------------------------------------------------------------
def search_and_format(
    query: str,
    api_key: str = SERPAPI_KEY,
    domain: str = AMAZON_DOMAIN,
    save: bool = True,
    filter_params: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    High-level wrapper: search → format → (optionally) save → return rows.

    Parameters
    ----------
    query : str
        Amazon search term.
    api_key : str
        SerpApi key.
    domain : str
        Amazon marketplace domain.
    save : bool
        If True, write raw JSON + formatted rows to disk.
    filter_params : dict, optional
        Additional Amazon search parameters (e.g. ``rh`` for refinement).

    Returns
    -------
    list[dict]
        Formatted rows (one dict per product).
    """
    # Step 1 — fetch
    raw: Optional[Dict[str, Any]] = fetch_amazon_data(query, api_key, domain, filter_params=filter_params)
    if raw is None:
        logger.error("Aborting: could not fetch data for '%s'.", query)
        return []

    # Step 2 — parse
    rows: List[Dict[str, Any]] = format_data_for_csv(raw)

    # Step 3 — persist (optional)
    if save:
        save_results(query, raw, rows)

    return rows


# ---------------------------------------------------------------------------
# API Key validation helper
# ---------------------------------------------------------------------------
def verify_api_key(api_key: str) -> Dict[str, Any]:
    """Check whether a SerpApi key is valid by making a minimal API call.

    Parameters
    ----------
    api_key : str
        The key to test.

    Returns
    -------
    Dict[str, Any]
        {"valid": bool, "error": str or None, "remaining": int or None}
    """
    import requests as _req

    if not api_key or api_key in ("YOUR_SERPAPI_KEY_HERE", "your_serpapi_key_here", "SAMPLE_MODE"):
        return {"valid": False, "error": "Placeholder key detected — replace with a real SerpApi key.", "remaining": None}

    try:
        # Minimal search request (1 credit) — search for a generic term
        client = Client(api_key=api_key)
        raw = client.search(engine="amazon", k="test", amazon_domain="amazon.com", gl="us", hl="en-us", num=1)
        if "error" in raw:
            return {"valid": False, "error": raw["error"], "remaining": None}
        # Check search metadata for remaining credits
        remaining = raw.get("search_metadata", {}).get("credits_remaining")
        return {"valid": True, "error": None, "remaining": remaining}
    except Exception as exc:
        err_str = str(exc)
        if "401" in err_str or "Unauthorized" in err_str:
            return {"valid": False, "error": "API key rejected (HTTP 401). Generate a new key at https://serpapi.com.", "remaining": None}
        if "403" in err_str or "Forbidden" in err_str:
            return {"valid": False, "error": "API key forbidden (HTTP 403). Check SerpApi account status.", "remaining": None}
        return {"valid": False, "error": err_str, "remaining": None}


# ---------------------------------------------------------------------------
# Discovery: Product Detail Fetch & Niche Term Extraction
# ---------------------------------------------------------------------------
def fetch_product_details(
    asin: str,
    api_key: str,
    domain: str = AMAZON_DOMAIN,
    max_retries: int = 2,
) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed product information for a single ASIN via the SerpApi
    ``amazon_product`` endpoint.

    Returns categories, bought_together, also_bought, and other metadata.
    """
    params: Dict[str, Any] = {
        "engine": "amazon_product",
        "amazon_domain": domain,
        "asin": asin,
    }
    for attempt in range(1, max_retries + 1):
        try:
            client = Client(api_key=api_key)
            raw: SerpResults = client.search(**params)
            if "error" in raw:
                logger.warning(
                    "Product detail error for %s (attempt %d/%d): %s",
                    asin, attempt, max_retries, raw["error"],
                )
                time.sleep(REQUEST_DELAY)
                continue
            logger.info("Product details fetched for ASIN %s", asin)
            return dict(raw)
        except Exception as exc:
            logger.warning(
                "Product detail fetch failed for %s (attempt %d/%d): %s",
                asin, attempt, max_retries, exc,
            )
            if attempt < max_retries:
                time.sleep(REQUEST_DELAY)
    return None


def _is_too_similar(title: str, query: str) -> bool:
    """Return True if *title* is essentially the same search as *query*."""
    q_words = set(query.lower().split())
    t_words = set(title.lower().split())
    if not q_words:
        return False
    overlap = len(q_words & t_words)
    return overlap >= len(q_words) - 1


def _extract_categories(
    details: Dict[str, Any],
    origin_asin: str,
    query: str,
) -> List[Dict[str, Any]]:
    """Extract category breadcrumb terms from a product detail response."""
    terms: List[Dict[str, Any]] = []
    raw = details.get("categories") or details.get("product_information", {}).get("categories", [])
    if isinstance(raw, list):
        for cat in raw:
            if isinstance(cat, dict):
                name = cat.get("name", "").strip()
            else:
                name = str(cat).strip()
            if name and not _is_too_similar(name, query):
                terms.append({
                    "term": name,
                    "source": "category",
                    "origin_asin": origin_asin,
                    "score": 90,
                })
    return terms


def _extract_bought_together(
    details: Dict[str, Any],
    origin_asin: str,
    query: str,
) -> List[Dict[str, Any]]:
    """Extract frequently-bought-together product titles."""
    terms: List[Dict[str, Any]] = []
    for key in ("bought_together", "frequently_bought_together"):
        raw = details.get(key, [])
        if isinstance(raw, list):
            for item in raw:
                title = (item.get("title") or "").strip()
                if title and not _is_too_similar(title, query):
                    terms.append({
                        "term": title[:100],
                        "source": "bought_together",
                        "origin_asin": origin_asin,
                        "score": 70,
                    })
    return terms


def _extract_also_bought(
    details: Dict[str, Any],
    origin_asin: str,
    query: str,
) -> List[Dict[str, Any]]:
    """Extract also-bought product titles."""
    terms: List[Dict[str, Any]] = []
    raw = details.get("also_bought", [])
    if isinstance(raw, list):
        for item in raw:
            title = (item.get("title") or "").strip()
            if title and not _is_too_similar(title, query):
                terms.append({
                    "term": title[:100],
                    "source": "also_bought",
                    "origin_asin": origin_asin,
                    "score": 40,
                })
    return terms


def extract_discovery_terms(
    query: str,
    top_asins: List[str],
    api_key: str,
    max_asins: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetch product-detail pages for the top N ASINs and extract niche
    discovery terms (categories, bought_together, also_bought).

    Each returned dict has keys:
        term, source, origin_asin, score

    Terms are deduplicated and sorted by score descending.
    Score range: 90 (direct category) -> 70 (bought together) -> 40 (also bought).
    """
    collector: Dict[str, Dict[str, Any]] = {}

    for asin in top_asins[:max_asins]:
        details = fetch_product_details(asin, api_key)
        if not details:
            continue

        extractors = [
            _extract_categories,
            _extract_bought_together,
            _extract_also_bought,
        ]
        for extractor in extractors:
            for term in extractor(details, asin, query):
                key = term["term"].lower()[:80]
                # Keep the highest score for each term
                if key not in collector or term["score"] > collector[key]["score"]:
                    collector[key] = term

    result = sorted(collector.values(), key=lambda x: x["score"], reverse=True)
    logger.info(
        "Discovery: extracted %d unique terms from %d product(s) for '%s'",
        len(result), len(top_asins[:max_asins]), query,
    )
    return result


# ---------------------------------------------------------------------------
# Provider-agnostic search — delegates to the active provider
# ---------------------------------------------------------------------------
def fetch_category_url(
    keyword: str,
    marketplace: str = "amz_us",
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Scrape Amazon search results using the currently active data provider.

    The active provider is determined by ``PROVIDER_ACTIVE`` in config.ini
    (default: ``"pangolinfo"``). This function delegates to the provider's
    ``.scrape()`` method, so swapping the provider requires zero code changes.

    Parameters
    ----------
    keyword : str
        Amazon search keyword.
    marketplace : str
        Marketplace slug (provider-specific; Pangolinfo uses ``amz_us`` etc.).
    max_retries : int
        Passed through to the provider.

    Returns
    -------
    dict or None
        Raw provider response, or None on failure.
    """
    from .providers import get_provider

    provider = get_provider()
    if not provider.is_configured():
        logger.error("Active provider '%s' is not configured.", provider.slug)
        return {
            "error": (
                f"Provider '{provider.name}' is not configured. "
                f"Set its credentials in config.ini or .env."
            )
        }

    logger.info(
        "fetch_category_url -> provider='%s' keyword='%s' marketplace=%s",
        provider.slug, keyword, marketplace,
    )
    return provider.scrape(keyword, marketplace=marketplace, max_retries=max_retries)


def normalize_pangolinfo_results(raw_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize a provider response into the unified schema.

    Delegates to the active provider's ``.normalize()`` method so the caller
    only sees ASIN, Title, Price, ReviewCount, Rating, Sales, etc. regardless
    of which provider is active.
    """
    from .providers import get_provider

    provider = get_provider()
    return provider.normalize(raw_json)


def tunnel_category_pages(
    url: str,
    api_key: str,
    max_pages: int = 5,
    page_delay: float = 2.0,
    save: bool = True,
) -> List[Dict[str, Any]]:
    """
    Iterate through multiple pages of an Amazon category / bestseller URL,
    extracting ASINs and metadata (Price, Rating) from each page.

    Uses the SerpApi ``url`` parameter and ``yield_pages()`` for pagination.

    Parameters
    ----------
    url : str
        Full Amazon category or bestseller URL.
    api_key : str
        Valid SerpApi key.
    max_pages : int
        Number of pages to traverse (default: 5).
    page_delay : float
        Seconds between page requests.
    save : bool
        If True, write raw + formatted JSON to disk under a safe filename
        derived from the URL.

    Returns
    -------
    list[dict]
        Deduplicated, formatted product rows.
    """
    all_items: List[Dict[str, Any]] = []
    seen_asins: set = set()

    params: Dict[str, Any] = {
        "engine": "amazon",
        "url": url,
    }

    client = Client(api_key=api_key)

    # Page 1
    for attempt in range(1, 4):
        try:
            logger.info("Tunnel — page 1/%d ...", max_pages)
            first_page = client.search(**params)
            if "error" in first_page:
                logger.error("Tunnel error on page 1: %s", first_page["error"])
                return []
            _merge_organic(first_page, all_items, seen_asins)
            logger.info(
                "Tunnel — page 1: %d items (%d unique)",
                len(first_page.get("organic_results", [])),
                len(all_items),
            )
            raw_responses = [dict(first_page)]
            break
        except Exception as exc:
            logger.warning("Tunnel page 1, attempt %d/3: %s", attempt, exc)
            if attempt < 3:
                time.sleep(REQUEST_DELAY)
            else:
                return []

    # Pages 2+ via yield_pages
    page_count = 1
    try:
        for next_page in first_page.yield_pages(max_pages):
            page_count += 1
            if page_count > max_pages:
                break
            if "error" in next_page:
                logger.warning("Tunnel page %d error: %s", page_count, next_page["error"])
                break
            _merge_organic(next_page, all_items, seen_asins)
            raw_responses.append(dict(next_page))
            logger.info(
                "Tunnel — page %d: %d items (%d unique)",
                page_count,
                len(next_page.get("organic_results", [])),
                len(all_items),
            )
            if page_count < max_pages:
                time.sleep(page_delay)
    except Exception as exc:
        logger.warning("Tunnel pagination stopped at page %d: %s", page_count, exc)

    logger.info(
        "Tunnel complete — %d pages, %d unique products.",
        page_count, len(all_items),
    )

    # Format into schema rows
    rows: List[Dict[str, Any]] = []
    for position, item in enumerate(all_items, start=1):
        try:
            rows.append({
                "ASIN": item.get("asin", "N/A"),
                "Title": (item.get("title") or "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": _extract_publication_date(item),
                "thumbnail": item.get("thumbnail", ""),
            })
        except Exception as exc:
            logger.warning("Skipping tunnel item %s: %s", item.get("asin", "?"), exc)

    # Optionally save
    if save and rows:
        safe_name = url.replace("https://", "").replace("/", "_")[:60].lower()
        combined = {
            "url": url,
            "total_pages": page_count,
            "total_unique": len(rows),
            "organic_results": all_items,
        }
        save_results(safe_name, combined, rows)

    logger.info("Tunnel formatted %d schema rows.", len(rows))
    return rows


def _merge_organic(
    response: SerpResults,
    target: List[Dict[str, Any]],
    seen: set,
) -> None:
    """Merge organic results from a single page response, deduping by ASIN."""
    for item in response.get("organic_results", []):
        asin = item.get("asin")
        if asin and asin not in seen:
            seen.add(asin)
            target.append(item)


# ---------------------------------------------------------------------------
# Deep Niche Tunneling — extract categories + build filtered search URLs
# ---------------------------------------------------------------------------
def extract_niche_from_asin(
    asin: str,
    api_key: str,
    domain: str = AMAZON_DOMAIN,
) -> Optional[Dict[str, Any]]:
    """
    Extract niche (category/browse node) information from a single ASIN
    via the SerpApi ``amazon_product`` endpoint.

    Returns a dict with keys:
      - asin: the source ASIN
      - category_name: human-readable category name (e.g. "Children's Cookbooks")
      - browse_node_id: Amazon browse node ID for URL construction
      - breadcrumb: full category breadcrumb list
      - url: raw product detail data for further analysis

    Returns ``None`` if the API call fails or no category is found.
    """
    details = fetch_product_details(asin, api_key, domain)
    if not details:
        return None

    categories_raw = details.get("categories") or details.get("product_information", {}).get("categories", [])
    if not categories_raw or not isinstance(categories_raw, list):
        return None

    # Pick the most specific (last) category with a browse node ID
    best: Optional[Dict[str, Any]] = None
    breadcrumb: List[str] = []
    for cat in categories_raw:
        name = (cat.get("name") or "").strip()
        node_id = cat.get("id") or cat.get("node_id") or ""
        if name:
            breadcrumb.append(name)
            if node_id:
                best = {
                    "category_name": name,
                    "browse_node_id": str(node_id),
                }

    if not best:
        # Fallback: use the last breadcrumb name even without node ID
        if breadcrumb:
            best = {
                "category_name": breadcrumb[-1],
                "browse_node_id": "",
            }
        else:
            return None

    best["asin"] = asin
    best["breadcrumb"] = breadcrumb
    best["url"] = details.get("product_link") or f"https://www.{domain}/dp/{asin}"
    logger.info(
        "Niche extracted from ASIN %s — '%s' (node: %s)",
        asin, best["category_name"], best["browse_node_id"],
    )
    return best


def generate_niche_search_url(
    niche_info: Dict[str, Any],
    last_30_days: bool = True,
    domain: str = AMAZON_DOMAIN,
) -> str:
    """
    Build an Amazon search URL from extracted niche information.

    Parameters
    ----------
    niche_info : dict
        Result from ``extract_niche_from_asin()`` — must contain
        ``category_name`` and optionally ``browse_node_id``.
    last_30_days : bool
        If True, append ``p_n_publication_date:1250226011`` to the
        ``rh`` refinement.
    domain : str
        Amazon marketplace domain.

    Returns
    -------
    str
        Full Amazon search URL with rh refinement parameters.
    """
    node_id = niche_info.get("browse_node_id", "")
    category_name = niche_info.get("category_name", "books")

    if node_id:
        rh_parts = [f"n:{node_id}"]
    else:
        # URL-encode the category name as a search fallback
        encoded_name = category_name.replace(" ", "+")
        rh_parts = [f"n:283155"]  # default to "Books" node

    if last_30_days:
        rh_parts.append("p_n_publication_date:1250226011")

    rh_str = ",".join(rh_parts)
    query_encoded = category_name.replace(" ", "+")
    url = (
        f"https://www.{domain}/s?"
        f"k={query_encoded}&rh={rh_str}"
    )
    logger.info(
        "Niche search URL generated — %s (node: %s, last_30_days: %s)",
        url, node_id, last_30_days,
    )
    return url


def generate_filtered_url(
    query: str,
    filter_type: str = 'new_30_days',
    domain: str = AMAZON_DOMAIN,
) -> tuple:
    """
    Generate filtered Amazon search URL + params pair for SerpApi.

    Returns (base_url, params_dict) so the caller can pass params directly
    to ``serpapi.Client.search()``.

    Parameters
    ----------
    query : str
        Amazon search keyword.
    filter_type : str
        ``'new_30_days'`` — appends ``n:283155,p_n_publication_date:1250226011``.
    domain : str
        Amazon marketplace domain.

    Returns
    -------
    tuple[ str, dict ]
        (base_url, params_dict) — URL for display, params for SerpApi.
    """
    base_url = f"https://www.{domain}/s"
    params: Dict[str, Any] = {
        "engine": "amazon",
        "amazon_domain": domain,
        "k": query.replace(" ", "+"),
        "i": "stripbooks",
        "ref": "nb_sb_noss",
    }
    if filter_type == 'new_30_days':
        params.update({
            "rh": "n:283155,p_n_publication_date:1250226011",
            "dc": "true",
        })
    logger.info("Filtered URL generated — query='%s', filter=%s", query, filter_type)
    return base_url, params


def deep_tunnel_niche(
    query: str,
    api_key: str,
    filter_type: str = 'new_30_days',
    domain: str = AMAZON_DOMAIN,
    max_pages: int = 3,
) -> List[Dict[str, Any]]:
    """
    Deep Tunnel into a niche: run a filtered Amazon search and return
    formatted product rows with EOS-friendly schema.

    Uses ``generate_filtered_url()`` + ``fetch_all_pages()`` internally.
    """
    _url, params = generate_filtered_url(query, filter_type, domain)
    client = Client(api_key=api_key)

    all_items: List[Dict[str, Any]] = []
    seen_asins: set = set()
    page_size = 20

    for page in range(1, max_pages + 1):
        params["start"] = (page - 1) * page_size
        for attempt in range(1, 4):
            try:
                raw = client.search(**params)
                if "error" in raw:
                    break
                organic = raw.get("organic_results", [])
                if not organic:
                    break
                for item in organic:
                    asin = item.get("asin")
                    if asin and asin not in seen_asins:
                        seen_asins.add(asin)
                        all_items.append(item)
                if page < max_pages:
                    time.sleep(REQUEST_DELAY)
                break
            except Exception as exc:
                if attempt < 3:
                    time.sleep(REQUEST_DELAY * (2 ** (attempt - 1)))
                else:
                    logger.warning("deep_tunnel_niche page %d failed: %s", page, exc)

    rows: List[Dict[str, Any]] = []
    for position, item in enumerate(all_items, start=1):
        try:
            rows.append({
                "ASIN": item.get("asin", "N/A"),
                "Title": (item.get("title") or "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": _extract_publication_date(item),
                "thumbnail": item.get("thumbnail", ""),
                "Position": position,
            })
        except Exception as exc:
            logger.warning("Skipping tunnel item %s: %s", item.get("asin", "?"), exc)

    logger.info("Deep tunnel complete — %d unique products for '%s'", len(rows), query)
    return rows


# ---------------------------------------------------------------------------
# BSR Enrichment — fetch real BSR from Product API (costs 1 credit/ASIN)
# ---------------------------------------------------------------------------
def extract_bsr_from_product_details(
    details: Dict[str, Any],
) -> Optional[int]:
    """
    Extract the Best Sellers Rank (BSR) from a SerpApi Product API response.

    The response can nest BSR in several locations; this function tries
    each in priority order:

      1. ``product_information.sellers[*].rank``  (first seller with a rank)
      2. ``product_information.sales_rank``        (direct numeric field)
      3. ``product_information.rank``              (alternative key)
      4. ``product_information.best_sellers_rank`` (verbose key)

    Parameters
    ----------
    details : dict
        Raw response from ``fetch_product_details()``.

    Returns
    -------
    int or None
        The numeric BSR value, or None if not found.
    """
    try:
        pi = details.get("product_information") or {}
    except Exception:
        pi = {}

    # Priority 1: seller rank (e.g. #12,345 in Books)
    try:
        sellers = pi.get("sellers", [])
        if isinstance(sellers, list):
            for seller in sellers:
                raw = seller.get("rank")
                if raw is not None:
                    val = _clean_bsr(raw)
                    if val is not None:
                        return val
    except Exception:
        pass

    # Priority 2-4: direct fields
    for key in ("sales_rank", "rank", "best_sellers_rank"):
        try:
            raw = pi.get(key)
            if raw is not None:
                val = _clean_bsr(raw)
                if val is not None:
                    return val
        except Exception:
            continue

    return None


def _clean_bsr(raw: Any) -> Optional[int]:
    """
    Convert a raw BSR value (string or int) to a clean integer.

    Handles formats like:
      - "#12,345 in Books"
      - "12,345"
      - 12345
    """
    try:
        if isinstance(raw, (int, float)):
            return int(raw)
        s = str(raw).replace(",", "").strip()
        # Extract the first number found
        import re
        match = re.search(r"#?(\d+)", s)
        if match:
            return int(match.group(1))
        # Fallback: try parsing the whole string
        if s and s.replace(" ", "").isdigit():
            return int(s)
    except Exception:
        pass
    return None


def enrich_row_with_bsr(
    row: Dict[str, Any],
    api_key: str,
    domain: str = AMAZON_DOMAIN,
) -> Dict[str, Any]:
    """
    Fetch BSR for a single product row and return the updated row.

    Uses the SerpApi ``amazon_product`` endpoint (1 credit per call).

    Parameters
    ----------
    row : dict
        A formatted product row (must contain ``ASIN``).
    api_key : str
        Valid SerpApi key.
    domain : str
        Amazon marketplace domain.

    Returns
    -------
    dict
        The same row with ``BSR`` field updated if data was found.
    """
    asin = row.get("ASIN", "")
    if not asin or asin == "N/A":
        return row

    details = fetch_product_details(asin, api_key, domain)
    if not details:
        return row

    bsr = extract_bsr_from_product_details(details)
    if bsr is not None:
        row["BSR"] = bsr
        logger.info("BSR for %s → %d", asin, bsr)
    else:
        logger.info("No BSR found for %s (BSR stays 0)", asin)

    return row


def batch_enrich_bsr(
    rows: List[Dict[str, Any]],
    api_key: str,
    max_asins: Optional[int] = None,
    domain: str = AMAZON_DOMAIN,
    delay: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Enrich a list of product rows with real BSR values from the Product API.

    Costs **1 SerpApi credit per ASIN** enriched. Use *max_asins* to
    limit total cost (e.g. 20 → 20 credits).

    Parameters
    ----------
    rows : list[dict]
        Formatted product rows (must contain ``ASIN``).
    api_key : str
        Valid SerpApi key.
    max_asins : int, optional
        Maximum number of ASINs to enrich. ``None`` = enrich all.
    domain : str
        Amazon marketplace domain.
    delay : float
        Seconds between API calls to avoid rate limits.

    Returns
    -------
    list[dict]
        Rows with updated ``BSR`` values.
    """
    target = rows[:max_asins] if max_asins else rows
    skipped = rows[len(target):] if max_asins else []

    logger.info(
        "BSR enrichment: %d ASIN(s) (%.1f credits total @ 1/ASIN)",
        len(target), len(target),
    )

    for i, row in enumerate(target):
        updated = enrich_row_with_bsr(row, api_key, domain)
        target[i] = updated
        if i < len(target) - 1:
            time.sleep(delay)

    result = target + skipped
    enriched = sum(1 for r in result if r.get("BSR", 0) > 0)
    logger.info(
        "BSR enrichment complete — %d/%d rows enriched.",
        enriched, len(rows),
    )
    return result


# ---------------------------------------------------------------------------
# Keyword Explorer — fetch Amazon search suggestions (free, no API key)
# ---------------------------------------------------------------------------
AMAZON_SUGGEST_URL = "https://completion.amazon.com/api/2017/suggestions?limit={limit}&prefix={query}&mid=ATVPDKIKX0DER&alias=stripbooks&suggestion-type=WIDGET&_={ts}"


def fetch_amazon_suggestions(query: str, limit: int = 10) -> List[str]:
    """
    Fetch autocomplete suggestions from Amazon's public completion API.
    No API key needed — uses the same endpoint as the search bar.

    Returns list of suggestion strings.
    """
    import requests as http_requests
    from urllib.parse import quote

    url = (
        "https://completion.amazon.com/api/2017/suggestions?"
        f"limit={limit}&prefix={quote(query)}"
        "&mid=ATVPDKIKX0DER&alias=stripbooks"
        "&suggestion-type=WIDGET"
        f"&_={int(time.time() * 1000)}"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.amazon.com/",
    }

    try:
        resp = http_requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        suggestions: List[str] = []
        for item in data.get("suggestions", []):
            value = item.get("value", "")
            if value and value.lower() != query.lower():
                suggestions.append(value)
        return suggestions[:limit]
    except Exception as exc:
        logger.warning("Failed to fetch Amazon suggestions for '%s': %s", query, exc)
        return []


# ---------------------------------------------------------------------------
# Category Browser — fetch Amazon browse node tree
# ---------------------------------------------------------------------------
def fetch_category_tree(domain: str = "amazon.com") -> List[Dict[str, Any]]:
    """
    Fetch a flat list of Amazon browse node categories using SerpApi.

    Returns list of {id, name, parent_id} dicts.
    Note: SerpApi free tier has limited category endpoints.
    This provides a curated fallback list of top-level KDP-relevant nodes.
    """
    # Curated top-level KDP book categories (stable browse nodes)
    categories = [
        {"id": "283155", "name": "Books", "parent_id": None},
        {"id": "173507", "name": "Arts & Photography", "parent_id": "283155"},
        {"id": "17439", "name": "Biographies & Memoirs", "parent_id": "283155"},
        {"id": "6", "name": "Business & Money", "parent_id": "283155"},
        {"id": "17", "name": "Comics & Graphic Novels", "parent_id": "283155"},
        {"id": "28", "name": "Computers & Technology", "parent_id": "283155"},
        {"id": "11401", "name": "Cookbooks, Food & Wine", "parent_id": "283155"},
        {"id": "48", "name": "Crafts, Hobbies & Home", "parent_id": "283155"},
        {"id": "55", "name": "Education & Teaching", "parent_id": "283155"},
        {"id": "297540", "name": "Genre Fiction", "parent_id": "283155"},
        {"id": "86", "name": "Health, Fitness & Dieting", "parent_id": "283155"},
        {"id": "89", "name": "History", "parent_id": "283155"},
        {"id": "91", "name": "Humor & Entertainment", "parent_id": "283155"},
        {"id": "10777", "name": "Literature & Fiction", "parent_id": "283155"},
        {"id": "11209", "name": "Mystery, Thriller & Suspense", "parent_id": "283155"},
        {"id": "185", "name": "Parenting & Relationships", "parent_id": "283155"},
        {"id": "337", "name": "Politics & Social Sciences", "parent_id": "283155"},
        {"id": "290060", "name": "Reference", "parent_id": "283155"},
        {"id": "22", "name": "Religion & Spirituality", "parent_id": "283155"},
        {"id": "10", "name": "Science & Math", "parent_id": "283155"},
        {"id": "11823", "name": "Science Fiction & Fantasy", "parent_id": "283155"},
        {"id": "2159", "name": "Self-Help", "parent_id": "283155"},
        {"id": "25", "name": "Sports & Outdoors", "parent_id": "283155"},
        {"id": "5267710011", "name": "Teen & Young Adult", "parent_id": "283155"},
        {"id": "20", "name": "Travel", "parent_id": "283155"},
        {"id": "5", "name": "Children's Books", "parent_id": "283155"},
    ]

    # Try to enrich via SerpApi if available
    api_key = os.environ.get("SERPAPI_KEY", "")
    if api_key and api_key != "YOUR_SERPAPI_KEY_HERE":
        try:
            from serpapi import Client as SerpClient
            logger.info("Fetching category tree from SerpApi...")
        except ImportError:
            pass

    return categories


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tier 1: Amazon KDP Data Gatherer")
    parser.add_argument("query", type=str, help="Search query (e.g. 'low fodmap cookbook for kids')")
    parser.add_argument("--domain", type=str, default=AMAZON_DOMAIN, help="Amazon domain (default: amazon.com)")
    parser.add_argument("--key", type=str, default=SERPAPI_KEY, help="SerpApi key (or set SERPAPI_KEY env var)")
    parser.add_argument("--no-save", action="store_true", help="Skip saving results to disk")

    args = parser.parse_args()

    if args.key == "YOUR_SERPAPI_KEY_HERE":
        logger.error(
            "No SerpApi key found. Set the SERPAPI_KEY environment variable "
            "or pass it with --key."
        )
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("KDP Research Pipeline — Tier 1: Gather")
    logger.info("Query: %s", args.query)
    logger.info("Domain: %s", args.domain)
    logger.info("=" * 60)

    results = search_and_format(query=args.query, api_key=args.key, domain=args.domain, save=not args.no_save)

    print("\n")
    print(f"{'ASIN':<15} {'Title':<55} {'Price':>8} {'★':>5} {'Reviews':>8}")
    print("-" * 95)
    for r in results[:10]:  # show first 10 in console
        title = r["Title"][:52] + ".." if len(r["Title"]) > 52 else r["Title"]
        print(f"{r['ASIN']:<15} {title:<55} {r['Price']:>8.2f} {r['Rating']:>5.1f} {r['ReviewCount']:>8}")

    print(f"\nTotal products found: {len(results)}")

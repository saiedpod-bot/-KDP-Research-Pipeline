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
import json
import time
import logging
from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime
from pathlib import Path

from serpapi import Client, SerpResults


# ---------------------------------------------------------------------------
# .env loader — keeps API keys out of version control
# Looks for a .env file in the project root (parent of src/).
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    with open(_ENV_PATH, encoding="utf-8") as _fh:
        for _line in _fh:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


# ---------------------------------------------------------------------------
# Logging setup — consistent across all pipeline modules
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "scraper.log", mode="a"),
    ],
)
logger = logging.getLogger("kdpscraper")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Reads from .env → env var → fallback placeholder.
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "YOUR_SERPAPI_KEY_HERE")

# Amazon marketplace domain — change per target region
AMAZON_DOMAIN: str = "amazon.com"

# Delay (seconds) between consecutive API calls to avoid rate limits
REQUEST_DELAY: float = 1.5

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

    Returns
    -------
    dict or None
        Raw SerpApi response JSON, or None if all retries fail.
    """
    params: Dict[str, Any] = {
        "engine": "amazon",
        "amazon_domain": domain,
        "k": query,                     # Amazon uses parameter 'k' not 'q'
        "gl": "us",
        "hl": "en-us",
    }

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

        for item in results:
            try:
                row = {
                    "ASIN": item.get("asin", "N/A"),
                    "Title": item.get("title", "").strip(),
                    "Author": _extract_author(item),
                    "Price": _parse_price(item),
                    "BSR": 0,                 # requires product-detail endpoint
                    "ReviewCount": _parse_review_count(item),
                    "Rating": _parse_rating(item),
                    "PublicationDate": "N/A", # requires product-detail endpoint
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

                # Respect rate limits
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
    for item in all_items:
        try:
            rows.append({
                "ASIN": item.get("asin", "N/A"),
                "Title": (item.get("title") or "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": "N/A",
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
        "k": query,                     # Amazon uses parameter 'k' not 'q'
        "gl": "us",
        "hl": "en-us",
    }

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
    )
    if not raw_responses:
        logger.error("Batch fetch returned 0 pages for '%s'.", query)
        return []

    merged_items = merge_organic_results(raw_responses)

    rows: List[Dict[str, Any]] = []
    parsed_ok = 0
    for item in merged_items:
        try:
            row = {
                "ASIN": item.get("asin", "N/A"),
                "Title": item.get("title", "").strip(),
                "Author": _extract_author(item),
                "Price": _parse_price(item),
                "BSR": 0,
                "ReviewCount": _parse_review_count(item),
                "Rating": _parse_rating(item),
                "PublicationDate": "N/A",
            }
            rows.append(row)
            parsed_ok += 1
        except Exception as exc:
            asin = item.get("asin", "UNKNOWN")
            logger.warning("Skipping item %s: %s", asin, exc)

    logger.info(
        "Formatted %d / %d merged items into schema rows.",
        parsed_ok,
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

    Returns
    -------
    list[dict]
        Formatted rows (one dict per product).
    """
    # Step 1 — fetch
    raw: Optional[Dict[str, Any]] = fetch_amazon_data(query, api_key, domain)
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

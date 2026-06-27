"""
pangolinfo.py — Pangolinfo API client implementing BaseProvider.

Endpoint:  https://scrapeapi.pangolinfo.com/api/v1/scrape (POST)
Auth:      Bearer token via ``PANGOLINFO_TOKEN`` env / config.
Parser:    ``amzKeyword`` — returns ``data.json[0].data.results``.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider

logger = logging.getLogger("kdpprovider.pangolinfo")

PANGOLINFO_API_URL: str = "https://scrapeapi.pangolinfo.com/api/v1/scrape"

# Marketplace slug map (Pangolinfo → Amazon domain)
_MARKETPLACE_MAP = {
    "amz_us": "amz_us",
    "amz_uk": "amz_uk",
    "amz_de": "amz_de",
    "amz_fr": "amz_fr",
    "amz_jp": "amz_jp",
    "amz_ca": "amz_ca",
    "amz_in": "amz_in",
    "amz_com_au": "amz_com_au",
    "amz_mx": "amz_mx",
    "amz_it": "amz_it",
    "amz_es": "amz_es",
}


class PangolinfoProvider(BaseProvider):
    """Provider implementation for the Pangolinfo Amazon Scrape API."""

    @property
    def name(self) -> str:
        return "Pangolinfo"

    @property
    def slug(self) -> str:
        return "pangolinfo"

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_token() -> str:
        """Check env, then fallback to module-level config."""
        return os.getenv("PANGOLINFO_TOKEN") or ""

    def is_configured(self) -> bool:
        return bool(self._resolve_token())

    # ------------------------------------------------------------------
    # Scrape
    # ------------------------------------------------------------------
    def scrape(self, keyword: str, marketplace: str = "amz_us", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute keyword search via Pangolinfo ``amzKeyword`` parser.

        Parameters
        ----------
        keyword : str
        marketplace : str
            One of the keys in ``_MARKETPLACE_MAP``.
        **kwargs
            ``max_retries`` (default 3).

        Returns
        -------
        dict or None
        """
        api_token = self._resolve_token()
        if not api_token:
            logger.error("PANGOLINFO_TOKEN is not configured.")
            return {"error": "PANGOLINFO_TOKEN missing."}

        max_retries = kwargs.get("max_retries", 3)
        site = _MARKETPLACE_MAP.get(marketplace, marketplace)

        payload = {
            "parserName": "amzKeyword",
            "site": site,
            "content": keyword,
            "format": "json",
        }
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "Pangolinfo scrape — keyword='%s' marketplace=%s (attempt %d/%d)",
                    keyword, marketplace, attempt, max_retries,
                )
                resp = requests.post(
                    PANGOLINFO_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("data", {}).get("json", [])
                    logger.info(
                        "Pangolinfo returned %d result groups for '%s'",
                        len(results), keyword,
                    )
                    return data
                logger.warning(
                    "Pangolinfo attempt %d/%d — HTTP %d: %s",
                    attempt, max_retries, resp.status_code, resp.text[:200],
                )
                if attempt < max_retries:
                    time.sleep(2)
            except requests.exceptions.Timeout:
                logger.warning("Pangolinfo timeout attempt %d/%d", attempt, max_retries)
                if attempt < max_retries:
                    time.sleep(2)
            except Exception as exc:
                logger.warning("Pangolinfo attempt %d/%d failed: %s", attempt, max_retries, exc)
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    logger.error("All %d attempts exhausted for '%s'", max_retries, keyword)
                    return None
        return None

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------
    def normalize(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize Pangolinfo response into unified schema.

        Expected structure::

            data.json[0].data.results

        Each result field: asin, title, price, star, rating, sales, image.
        """
        items: List[Dict[str, Any]] = []
        try:
            json_list = raw.get("data", {}).get("json", [])
            if not json_list:
                logger.warning("Pangolinfo response has no 'data.json' array.")
                return items
            results = json_list[0].get("data", {}).get("results", [])
            if not results:
                logger.warning("Pangolinfo results empty.")
                return items
        except (AttributeError, IndexError, TypeError) as exc:
            logger.error("Unexpected Pangolinfo structure: %s", exc)
            return items

        for raw_item in results:
            try:
                asin = raw_item.get("ASIN") or raw_item.get("asin") or raw_item.get("parentAsin", "N/A")
                title = raw_item.get("Title") or raw_item.get("title") or ""
                author = raw_item.get("Author") or raw_item.get("author") or "Unknown"

                price = raw_item.get("Price") or raw_item.get("price", 0) or 0
                if isinstance(price, str):
                    price = float(price.replace("$", "").replace(",", "").strip() or 0)

                review_raw = str(raw_item.get("Rating") or raw_item.get("rating") or "0")
                review_count = int("".join(c for c in review_raw if c.isdigit()) or 0)

                rating_raw = str(raw_item.get("Star") or raw_item.get("star") or "0")
                rating = float("".join(c for c in rating_raw if c.isdigit() or c == ".") or 0)

                sales = raw_item.get("Sales") or raw_item.get("sales", 0) or 0
                if isinstance(sales, str):
                    sales = int("".join(c for c in sales if c.isdigit()) or 0)

                thumbnail = raw_item.get("ImageUrl") or raw_item.get("imageUrl") or raw_item.get("image") or ""

                items.append({
                    "ASIN": asin,
                    "Title": title.strip(),
                    "Author": author,
                    "Price": price,
                    "BSR": 0,
                    "ReviewCount": review_count,
                    "Rating": rating,
                    "PublicationDate": raw_item.get("PublicationDate", raw_item.get("publicationDate", "")),
                    "Position": len(items) + 1,
                    "thumbnail": thumbnail,
                    "Sales": sales,
                })
            except Exception as exc:
                logger.warning("Skipping Pangolinfo item: %s", exc)
                continue

        logger.info("Normalized %d Pangolinfo items.", len(items))
        return items

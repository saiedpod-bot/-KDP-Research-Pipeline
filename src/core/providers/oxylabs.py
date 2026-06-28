"""
oxylabs.py — Oxylabs Real-Time Crawler API client.

Endpoint:      POST https://realtime.oxylabs.io/v1/queries
Auth:          Basic Auth (OXYLABS_USERNAME : OXYLABS_PASSWORD)
Source types:  amazon_search, amazon_product, amazon_bestsellers
"""

import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider

logger = logging.getLogger("kdpprovider.oxylabs")

OXYLABS_API_URL = "https://realtime.oxylabs.io/v1/queries"

_SOURCE_TYPE_SEARCH = "amazon_search"
_SOURCE_TYPE_PRODUCT = "amazon_product"
_SOURCE_TYPE_BESTSELLERS = "amazon_bestsellers"

# Marketplace domain → Oxylabs domain code
_MARKETPLACE_DOMAIN = {
    "amz_us": "com",
    "amz_uk": "co.uk",
    "amz_de": "de",
    "amz_fr": "fr",
    "amz_jp": "co.jp",
    "amz_ca": "ca",
    "amz_in": "in",
    "amz_com_au": "com.au",
    "amz_mx": "com.mx",
    "amz_it": "it",
    "amz_es": "es",
}


class OxylabsProvider(BaseProvider):
    """Provider implementation for Oxylabs Real-Time Crawler."""

    @property
    def name(self) -> str:
        return "Oxylabs"

    @property
    def slug(self) -> str:
        return "oxylabs"

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_username() -> str:
        return os.getenv("OXYLABS_USERNAME") or ""

    @staticmethod
    def _resolve_password() -> str:
        return os.getenv("OXYLABS_PASSWORD") or ""

    def is_configured(self) -> bool:
        return bool(self._resolve_username() and self._resolve_password())

    def _auth_header(self) -> Dict[str, str]:
        user = self._resolve_username()
        pwd = self._resolve_password()
        token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    # ------------------------------------------------------------------
    # Scrape
    # ------------------------------------------------------------------
    def scrape(self, keyword: str, marketplace: str = "amz_us", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute a keyword search via Oxylabs ``amazon_search`` source.

        Parameters
        ----------
        keyword : str
        marketplace : str
            One of ``_MARKETPLACE_DOMAIN`` keys.
        **kwargs
            ``source`` (default ``amazon_search``), ``max_retries`` (3),
            ``parse`` (True).

        Returns
        -------
        dict or None
            Wrapped with ``data.json[0].data.results`` for normalizer compat.
        """
        if not self.is_configured():
            logger.error("OXYLABS_USERNAME / OXYLABS_PASSWORD not configured.")
            return {"error": "Oxylabs credentials missing."}

        source = kwargs.get("source", _SOURCE_TYPE_SEARCH)
        domain = _MARKETPLACE_DOMAIN.get(marketplace, "com")
        parse = kwargs.get("parse", True)
        max_retries = kwargs.get("max_retries", 3)

        payload: Dict[str, Any] = {
            "source": source,
            "domain": domain,
            "parse": parse,
        }

        if source == _SOURCE_TYPE_SEARCH:
            payload["query"] = keyword
        elif source == _SOURCE_TYPE_PRODUCT:
            payload["query"] = keyword  # ASIN or search
        elif source == _SOURCE_TYPE_BESTSELLERS:
            payload["query"] = keyword  # category browse-node or keyword
        else:
            payload["query"] = keyword

        headers = self._auth_header()

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "Oxylabs scrape — source=%s keyword='%s' domain=%s (attempt %d/%d)",
                    source, keyword, domain, attempt, max_retries,
                )
                resp = requests.post(
                    OXYLABS_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    logger.info(
                        "Oxylabs returned %d result groups for '%s'",
                        len(results), keyword,
                    )
                    # Wrap in provider-agnostic envelope
                    return self._wrap_response(data)
                else:
                    logger.warning(
                        "Oxylabs attempt %d/%d — HTTP %d: %s",
                        attempt, max_retries, resp.status_code, resp.text[:300],
                    )
                    if attempt < max_retries:
                        time.sleep(3)
            except requests.exceptions.Timeout:
                logger.warning("Oxylabs timeout attempt %d/%d", attempt, max_retries)
                if attempt < max_retries:
                    time.sleep(3)
            except Exception as exc:
                logger.warning("Oxylabs attempt %d/%d failed: %s", attempt, max_retries, exc)
                if attempt < max_retries:
                    time.sleep(3)
                else:
                    logger.error("All %d attempts exhausted for '%s'", max_retries, keyword)
                    return None
        return None

    @staticmethod
    def _wrap_response(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrap Oxylabs response into the provider-agnostic envelope.

        Oxylabs ``amazon_search`` with ``parse=True`` returns::

            results[0].content.results = {
                "organic": [...],
                "amazons_choices": [...],
                "paid": [...],
                "suggested": [...],
            }

        We merge ``organic`` (primary) + ``amazons_choices`` +
        ``paid`` (sponsored) into a single flat ``results`` list.
        """
        oxy_results = raw.get("results", [])
        all_items: List[Dict[str, Any]] = []
        for group in oxy_results:
            content = group.get("content", {})
            sections = content.get("results", {})
            if isinstance(sections, dict):
                for section_key in ("organic", "amazons_choices", "paid", "suggested"):
                    section_items = sections.get(section_key, [])
                    if isinstance(section_items, list):
                        all_items.extend(section_items)
            elif isinstance(sections, list):
                all_items.extend(sections)
        return {
            "provider": "oxylabs",
            "data": {
                "json": [{"data": {"results": all_items}}],
            },
        }

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------
    def normalize(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize an Oxylabs parsed response into the unified schema.

        Oxylabs ``amazon_search`` with ``parse=True`` product schema::

            asin, title, price, rating (star float), reviews_count,
            url_image, is_sponsored, is_prime, best_seller
        """
        items: List[Dict[str, Any]] = []
        try:
            json_list = raw.get("data", {}).get("json", [])
            if not json_list:
                logger.warning("Oxylabs response has no data.json array.")
                return items
            results = json_list[0].get("data", {}).get("results", [])
        except (AttributeError, IndexError, TypeError) as exc:
            logger.error("Unexpected Oxylabs structure: %s", exc)
            return items

        for raw_item in results:
            try:
                asin = str(raw_item.get("asin", "N/A") or "N/A")
                title = raw_item.get("title") or ""
                price = raw_item.get("price", 0) or 0
                if isinstance(price, str):
                    price = float(price.replace("$", "").replace(",", "").strip() or 0)

                # Oxylabs uses "rating" for star rating (float) and "reviews_count" for count
                rating = float(raw_item.get("rating", 0) or 0)
                review_count = int(raw_item.get("reviews_count", 0) or 0)

                sales = raw_item.get("sales", 0) or 0
                if isinstance(sales, str):
                    sales = int("".join(c for c in sales if c.isdigit()) or 0)

                thumbnail = raw_item.get("url_image") or raw_item.get("image", "")

                brand = raw_item.get("brand") or raw_item.get("manufacturer") or ""

                items.append({
                    "ASIN": asin,
                    "Title": title.strip(),
                    "Author": brand or "Unknown",
                    "Price": price,
                    "BSR": 0,
                    "ReviewCount": review_count,
                    "Rating": rating,
                    "PublicationDate": "",
                    "Position": len(items) + 1,
                    "thumbnail": thumbnail,
                    "Sales": sales,
                })
            except Exception as exc:
                logger.warning("Skipping Oxylabs item: %s", exc)
                continue

        logger.info("Normalized %d Oxylabs items.", len(items))
        return items

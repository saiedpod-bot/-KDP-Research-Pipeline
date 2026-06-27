"""
apify.py — Apify Amazon Product Scraper client.

Uses the ``junglee/Amazon-crawler`` actor (or a configurable alternative)
to scrape Amazon search results.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseProvider

logger = logging.getLogger("kdpprovider.apify")

APIFY_API_BASE = "https://api.apify.com/v2"

# Default actor — may be overridden via APIFY_ACTOR_ID env var
_DEFAULT_ACTOR_ID = "BG3WDrGdteHgZgbPK"

# Marketplace → Amazon domain map
_MARKETPLACE_DOMAIN = {
    "amz_us": "www.amazon.com",
    "amz_uk": "www.amazon.co.uk",
    "amz_de": "www.amazon.de",
    "amz_fr": "www.amazon.fr",
    "amz_jp": "www.amazon.co.jp",
    "amz_ca": "www.amazon.ca",
    "amz_in": "www.amazon.in",
    "amz_com_au": "www.amazon.com.au",
    "amz_mx": "www.amazon.com.mx",
    "amz_it": "www.amazon.it",
    "amz_es": "www.amazon.es",
}


class ApifyProvider(BaseProvider):
    """Provider implementation for Apify's Amazon Product Scraper."""

    @property
    def name(self) -> str:
        return "Apify"

    @property
    def slug(self) -> str:
        return "apify"

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_token() -> str:
        return os.getenv("APIFY_TOKEN") or ""

    @staticmethod
    def _resolve_actor_id() -> str:
        return os.getenv("APIFY_ACTOR_ID") or _DEFAULT_ACTOR_ID

    def is_configured(self) -> bool:
        return bool(self._resolve_token())

    # ------------------------------------------------------------------
    # Scrape
    # ------------------------------------------------------------------
    def scrape(self, keyword: str, marketplace: str = "amz_us", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute keyword search via the Apify Amazon crawler.

        Builds an Amazon search URL from the keyword and marketplace,
        starts an actor run, waits for completion, and returns the
        dataset items wrapped in a provider-agnostic envelope.

        Parameters
        ----------
        keyword : str
        marketplace : str
            One of the keys in ``_MARKETPLACE_DOMAIN``.
        **kwargs
            ``max_pages`` (default 1).
            ``wait_secs`` (default 60) — max seconds to wait for run completion.

        Returns
        -------
        dict
            Wrapped response with ``data.json[0].data.results`` structure
            for compatibility with the normalizer.
        """
        token = self._resolve_token()
        if not token:
            logger.error("APIFY_TOKEN is not configured.")
            return {"error": "APIFY_TOKEN missing."}

        actor_id = self._resolve_actor_id()
        domain = _MARKETPLACE_DOMAIN.get(marketplace, "www.amazon.com")
        max_pages = kwargs.get("max_pages", 1)
        wait_secs = kwargs.get("wait_secs", 120)

        # Build Amazon search URL from keyword
        search_url = f"https://{domain}/s?k={requests.utils.quote(keyword)}"

        payload = {
            "categoryOrProductUrls": [{"url": search_url}],
            "maxSearchPagesPerStartUrl": max_pages,
            "maxItemsPerStartUrl": 100,
            "maxOffers": 0,
            "maxProductVariantsAsSeparateResults": 0,
            "proxyCountry": "AUTO_SELECT_PROXY_COUNTRY",
            "scrapeProductDetails": True,
            "scrapeProductVariantPrices": False,
            "scrapeSellers": False,
            "useCaptchaSolver": False,
        }

        logger.info(
            "Apify starting run — actor=%s keyword='%s' domain=%s",
            actor_id, keyword, domain,
        )

        try:
            # Start the run
            run_url = f"{APIFY_API_BASE}/acts/{actor_id}/runs"
            resp = requests.post(
                run_url,
                params={"token": token},
                json=payload,
                timeout=30,
            )
            if resp.status_code not in (200, 201):
                logger.error("Apify start-run failed: HTTP %d", resp.status_code)
                return {"error": f"Apify start-run failed: HTTP {resp.status_code}"}

            run_data = resp.json().get("data", {})
            run_id = run_data.get("id")
            if not run_id:
                logger.error("Apify run ID not in response.")
                return {"error": "Apify run ID missing."}

            logger.info("Apify run started: %s", run_id)

            # Poll for completion
            status_url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
            deadline = time.time() + wait_secs
            last_status = None
            while time.time() < deadline:
                sr = requests.get(status_url, params={"token": token}, timeout=15)
                if sr.status_code == 200:
                    status = sr.json().get("data", {}).get("status", "UNKNOWN")
                    if status != last_status:
                        logger.info("Apify run %s — status: %s", run_id, status)
                        last_status = status
                    if status == "SUCCEEDED":
                        break
                    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        logger.error("Apify run %s ended with status: %s", run_id, status)
                        return {
                            "error": f"Apify run failed: {status}",
                            "provider": "apify",
                        }
                time.sleep(3)

            if last_status != "SUCCEEDED":
                logger.warning("Apify run %s did not complete within %ds", run_id, wait_secs)
                return {"error": f"Apify run timed out after {wait_secs}s"}

            # Fetch dataset items
            dataset_id = sr.json().get("data", {}).get("defaultDatasetId")
            if not dataset_id:
                logger.error("Apify run has no dataset ID.")
                return {"error": "Apify dataset ID missing."}

            items_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
            ir = requests.get(
                items_url,
                params={"token": token, "format": "json"},
                timeout=30,
            )
            if ir.status_code != 200:
                logger.error("Apify dataset fetch failed: HTTP %d", ir.status_code)
                return {"error": f"Apify dataset fetch: HTTP {ir.status_code}"}

            items = ir.json()
            logger.info("Apify returned %d items for '%s'", len(items), keyword)

            # Wrap in a structure compatible with the normalizer
            return {
                "provider": "apify",
                "data": {
                    "json": [
                        {
                            "data": {
                                "results": items,
                            }
                        }
                    ]
                },
            }

        except requests.exceptions.Timeout:
            logger.error("Apify request timed out.")
            return {"error": "Apify request timed out."}
        except Exception as exc:
            logger.error("Apify scrape failed: %s", exc)
            return {"error": f"Apify scrape failed: {exc}"}

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------
    def normalize(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize Apify dataset items into the unified schema.

        Apify schema (common fields)::

            asin, title, price.value, stars, reviewsCount,
            url, mainImage, sales, author, brand
        """
        items: List[Dict[str, Any]] = []

        try:
            json_list = raw.get("data", {}).get("json", [])
            if not json_list:
                logger.warning("Apify response has no data.json array.")
                return items
            results = json_list[0].get("data", {}).get("results", [])
        except (AttributeError, IndexError, TypeError) as exc:
            logger.error("Unexpected Apify structure: %s", exc)
            return items

        for raw_item in results:
            try:
                asin = raw_item.get("asin") or raw_item.get("originalAsin", "N/A")
                title = raw_item.get("title") or ""
                author = raw_item.get("author") or raw_item.get("brand") or "Unknown"

                price_obj = raw_item.get("price", {}) or {}
                if isinstance(price_obj, dict):
                    price = float(price_obj.get("value", 0) or 0)
                else:
                    price = float(str(price_obj).replace("$", "").replace(",", "").strip() or 0)

                review_count = int(raw_item.get("reviewsCount", 0) or 0)
                stars = float(raw_item.get("stars", 0) or 0)

                sales = raw_item.get("sales", 0) or 0
                if isinstance(sales, str):
                    sales = int("".join(c for c in sales if c.isdigit()) or 0)

                thumbnail = raw_item.get("mainImage") or raw_item.get("image", "")

                items.append({
                    "ASIN": asin,
                    "Title": title.strip(),
                    "Author": author,
                    "Price": price,
                    "BSR": 0,
                    "ReviewCount": review_count,
                    "Rating": stars,
                    "PublicationDate": raw_item.get("publicationDate", ""),
                    "Position": len(items) + 1,
                    "thumbnail": thumbnail,
                    "Sales": sales,
                })
            except Exception as exc:
                logger.warning("Skipping Apify item: %s", exc)
                continue

        logger.info("Normalized %d Apify items.", len(items))
        return items

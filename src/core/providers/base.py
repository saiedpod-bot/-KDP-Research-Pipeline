"""
base.py — Abstract provider interface for Amazon data scraping.

Every provider must implement ``BaseProvider`` so the application can
swap data sources (Pangolinfo, Apify, ScraperAPI, …) without changing
business logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseProvider(ABC):
    """
    Unified interface that every data provider must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'Pangolinfo', 'Apify')."""

    @property
    @abstractmethod
    def slug(self) -> str:
        """Internal slug for config (e.g. 'pangolinfo', 'apify')."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider's credentials are available."""

    @abstractmethod
    def scrape(self, keyword: str, marketplace: str = "amz_us", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute a keyword search against the provider.

        Parameters
        ----------
        keyword : str
            Amazon search term.
        marketplace : str
            Marketplace identifier (provider-specific).
        **kwargs
            Provider-specific overrides.

        Returns
        -------
        dict or None
            Raw provider response. Must contain a ``data`` key with a
            ``results`` list at minimum (structure may vary by provider —
            the normalizer handles transformations).
        """

    @abstractmethod
    def normalize(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert a raw provider response into the unified schema:

            ASIN, Title, Author, Price, BSR, ReviewCount, Rating,
            PublicationDate, Position, thumbnail, Sales

        Parameters
        ----------
        raw : dict
            Response from ``.scrape()``.

        Returns
        -------
        list[dict]
            Normalized product rows in the unified schema.
        """

    def status(self) -> Dict[str, Any]:
        """
        Return diagnostic info about the provider.

        Override to include credit balance, rate-limit info, etc.
        """
        return {
            "name": self.name,
            "slug": self.slug,
            "configured": self.is_configured(),
        }

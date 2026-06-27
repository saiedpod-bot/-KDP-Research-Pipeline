"""
registry.py — Provider registry and factory.

The active provider is determined by the ``PROVIDER_ACTIVE`` environment
variable (set in config.ini or .env). Fallback is ``pangolinfo``.
"""
import os
import logging
from typing import Dict, List, Optional, Type

from .base import BaseProvider
from .pangolinfo import PangolinfoProvider
from .apify import ApifyProvider

logger = logging.getLogger("kdpprovider.registry")

# ---------------------------------------------------------------------------
# Registry: slug → provider class
# ---------------------------------------------------------------------------
_BUILTIN_PROVIDERS: Dict[str, Type[BaseProvider]] = {
    "pangolinfo": PangolinfoProvider,
    "apify": ApifyProvider,
}

# Cached singleton instances
_instances: Dict[str, BaseProvider] = {}


def register_provider(slug: str, cls: Type[BaseProvider]) -> None:
    """
    Register a custom provider class at runtime.

    Parameters
    ----------
    slug : str
        Unique identifier (must match ``PROVIDER_ACTIVE`` value).
    cls : Type[BaseProvider]
        Provider class implementing the ``BaseProvider`` interface.
    """
    _BUILTIN_PROVIDERS[slug] = cls
    logger.info("Registered provider '%s' (%s)", slug, cls.__name__)


def get_provider(slug: Optional[str] = None) -> BaseProvider:
    """
    Return the active (or requested) provider instance.

    Parameters
    ----------
    slug : str, optional
        Provider slug. If ``None``, reads from ``PROVIDER_ACTIVE`` env var
        (defaults to ``"pangolinfo"``).

    Returns
    -------
    BaseProvider
        Singleton instance of the requested provider.
    """
    if slug is None:
        slug = os.getenv("PROVIDER_ACTIVE", "pangolinfo").strip().lower()

    instance = _instances.get(slug)
    if instance is not None:
        return instance

    cls = _BUILTIN_PROVIDERS.get(slug)
    if cls is None:
        available = ", ".join(_BUILTIN_PROVIDERS)
        logger.warning(
            "Unknown provider '%s'. Falling back to 'pangolinfo'. "
            "Available: %s",
            slug, available,
        )
        cls = _BUILTIN_PROVIDERS["pangolinfo"]

    instance = cls()
    _instances[slug] = instance
    return instance


def list_providers() -> List[Dict[str, str]]:
    """
    Return metadata for all registered providers.

    Returns
    -------
    list[dict]
        Each item: ``{"slug": str, "name": str, "configured": bool}``.
    """
    result = []
    for slug, cls in _BUILTIN_PROVIDERS.items():
        instance = _instances.get(slug) or cls()
        result.append({
            "slug": slug,
            "name": instance.name,
            "configured": instance.is_configured(),
        })
    return result

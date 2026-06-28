"""
registry.py — Provider registry, factory, and task-based router.

The active provider is determined by the ``PROVIDER_ACTIVE`` environment
variable (set in config.ini or .env). Fallback is ``pangolinfo``.

The router (``get_scraper_for_task``) selects a provider based on task
urgency and data criticality, with automatic fallback on failure.
"""
import os
import logging
import random
from typing import Callable, Dict, List, Optional, Tuple, Type

from .base import BaseProvider
from .pangolinfo import PangolinfoProvider
from .apify import ApifyProvider
from .oxylabs import OxylabsProvider

logger = logging.getLogger("kdpprovider.registry")

# ---------------------------------------------------------------------------
# Registry: slug → provider class
# ---------------------------------------------------------------------------
_BUILTIN_PROVIDERS: Dict[str, Type[BaseProvider]] = {
    "pangolinfo": PangolinfoProvider,
    "apify": ApifyProvider,
    "oxylabs": OxylabsProvider,
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


# ---------------------------------------------------------------------------
# Task-based Provider Router
# ---------------------------------------------------------------------------
# Task categories that determine provider selection:
_TASK_URGENT = "urgent"        # Autocomplete / pre-search — use cheapest/fastest
_TASK_DEEP = "deep"            # Full analysis — use most reliable/rich data

# Priority-ordered fallback chains per task type:
# (slug, condition_check) — first configured match wins
_FALLBACK_CHAINS: Dict[str, List[Tuple[str, Callable[[], bool]]]] = {
    _TASK_URGENT: [
        ("pangolinfo", lambda: get_provider("pangolinfo").is_configured()),
        ("apify", lambda: get_provider("apify").is_configured()),
    ],
    _TASK_DEEP: [
        ("oxylabs", lambda: get_provider("oxylabs").is_configured()),
        ("pangolinfo", lambda: get_provider("pangolinfo").is_configured()),
        ("apify", lambda: get_provider("apify").is_configured()),
    ],
}


def get_scraper_for_task(
    task_type: str = _TASK_DEEP,
    preferred: Optional[str] = None,
    enable_fallback: bool = True,
) -> BaseProvider:
    """
    Select the best available provider for a given task type.

    Parameters
    ----------
    task_type : str
        ``"urgent"`` (fast/cheap) or ``"deep"`` (reliable/rich).
    preferred : str, optional
        Force a specific provider slug. If unset or fails, fallback chain
        is tried.
    enable_fallback : bool
        If True (default), automatically try each provider in the
        fallback chain until one succeeds.

    Returns
    -------
    BaseProvider
        The selected provider instance.
    """
    chain = _FALLBACK_CHAINS.get(task_type, _FALLBACK_CHAINS[_TASK_DEEP])

    # If preferred is given and configured, use it
    if preferred:
        try:
            p = get_provider(preferred)
            if p.is_configured():
                logger.info("Router: using preferred provider '%s' for %s", preferred, task_type)
                return p
            logger.warning("Router: preferred '%s' not configured, falling back.", preferred)
        except Exception:
            logger.warning("Router: preferred '%s' unavailable, falling back.", preferred)

    if not enable_fallback:
        # Return the first configured provider in the chain
        for slug, check in chain:
            if check():
                logger.info("Router: selected '%s' for %s", slug, task_type)
                return get_provider(slug)
        # Absolute fallback
        logger.warning("Router: no configured provider for %s, using default.", task_type)
        return get_provider("pangolinfo")

    # Try each provider in sequence
    failures: List[str] = []
    for slug, check in chain:
        if check():
            try:
                p = get_provider(slug)
                # Quick connectivity test by checking status
                logger.info("Router: trying '%s' for %s", slug, task_type)
                return p
            except Exception as exc:
                failures.append(f"{slug}({exc})")
        else:
            failures.append(f"{slug}(not-configured)")

    logger.warning(
        "Router: all providers failed for %s: %s. Using default.",
        task_type, "; ".join(failures),
    )
    return get_provider("pangolinfo")


def execute_with_fallback(
    keyword: str,
    marketplace: str = "amz_us",
    task_type: str = _TASK_DEEP,
    **kwargs,
) -> Dict:
    """
    High-level convenience: select provider via router, scrape, and
    auto-fallback to the next provider on failure.

    Parameters
    ----------
    keyword : str
    marketplace : str
    task_type : str
    **kwargs
        Passed through to ``provider.scrape()``.

    Returns
    -------
    dict
        Raw provider response, or ``{"error": ...}`` if all fail.
    """
    chain = _FALLBACK_CHAINS.get(task_type, _FALLBACK_CHAINS[_TASK_DEEP])
    errors: List[str] = []

    for slug, check in chain:
        if not check():
            errors.append(f"{slug}(not-configured)")
            continue
        try:
            provider = get_provider(slug)
            logger.info(
                "Fallback: trying '%s' for keyword='%s' task=%s",
                slug, keyword, task_type,
            )
            # Cache-aware scrape via get_or_scrape
            from ..cache import get_or_scrape
            result = get_or_scrape(
                query=keyword,
                provider_slug=slug,
                scrape_fn=lambda: provider.scrape(keyword, marketplace=marketplace, **kwargs),
            )
            if result is not None and "error" not in result:
                logger.info("Fallback: '%s' succeeded for '%s'", slug, keyword)
                return result
            err_msg = result.get("error", "None") if isinstance(result, dict) else str(result)
            errors.append(f"{slug}({err_msg})")
            logger.warning("Fallback: '%s' failed: %s", slug, err_msg)
        except Exception as exc:
            errors.append(f"{slug}({exc})")
            logger.warning("Fallback: '%s' exception: %s", slug, exc)

    logger.error("All providers failed for keyword='%s': %s", keyword, "; ".join(errors))
    return {"error": f"All providers failed: {'; '.join(errors)}"}

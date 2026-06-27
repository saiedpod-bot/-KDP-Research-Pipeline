"""
providers — Pluggable data-provider abstraction layer.

Each provider implements ``BaseProvider`` and is registered in the
``registry``. The active source is selected via the ``PROVIDER_ACTIVE``
environment variable (config.ini or .env).

Usage::

    from core.providers import get_provider
    provider = get_provider()           # reads PROVIDER_ACTIVE
    raw = provider.scrape("coloring book")
    products = provider.normalize(raw)
"""

from .base import BaseProvider
from .registry import get_provider, list_providers, register_provider
from .pangolinfo import PangolinfoProvider
from .apify import ApifyProvider

__all__ = [
    "BaseProvider",
    "PangolinfoProvider",
    "ApifyProvider",
    "get_provider",
    "list_providers",
    "register_provider",
]

"""
core/__init__.py -- KDP Research Pipeline Core Package

Exposes pipeline modules and shared utilities.
All core logic lives here, separated from the UI layer (app.py).
"""

from . import scraper
from . import analyzer
from . import exporter
from . import database
from . import config_manager

__all__ = ["scraper", "analyzer", "exporter", "database", "config_manager"]

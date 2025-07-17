"""
NERC Outages Domain

This module provides the public API for loading and working with NERC outages data.
"""

from .loader import load_from_file, load_from_url, DEFAULT_OUTAGES_FILE, DEFAULT_OUTAGES_URL
from .models import Outages, OutageItem, OutageTimeFrames

__all__ = [
    "load_from_file",
    "load_from_url",
    "DEFAULT_OUTAGES_FILE",
    "DEFAULT_OUTAGES_URL",
    "Outages",
    "OutageItem",
    "OutageTimeFrames",
]

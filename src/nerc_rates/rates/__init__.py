"""
NERC Rates Domain

This module provides the public API for loading and working with NERC rates data.
"""

from .loader import load_from_file, load_from_url, DEFAULT_RATES_FILE, DEFAULT_RATES_URL
from .models import Rates, RateItem, RateValue, RateType

__all__ = [
    "load_from_file",
    "load_from_url",
    "DEFAULT_RATES_FILE",
    "DEFAULT_RATES_URL",
    "Rates",
    "RateItem",
    "RateValue",
    "RateType",
]

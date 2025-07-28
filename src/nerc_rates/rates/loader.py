"""
NERC Rates Data Loading

This module provides functions to load and validate rates data from various sources.
Uses the generic DataLoader with dependency injection to eliminate code duplication.
"""

from ..base import create_loader
from .models import Rates

# Configuration constants
DEFAULT_RATES_FILE = "rates.yaml"
DEFAULT_RATES_URL = (
    "https://raw.githubusercontent.com/CCI-MOC/nerc-rates/main/rates.yaml"
)

# Create configured loader using dependency injection
_loader = create_loader(Rates, DEFAULT_RATES_URL, DEFAULT_RATES_FILE)

# Expose the loader functions with proper typing
load_from_url = _loader.load_from_url
load_from_file = _loader.load_from_file

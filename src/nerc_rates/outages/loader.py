"""
NERC Outages Data Loading

This module provides functions to load and validate outages data from various sources.
Uses the generic DataLoader with dependency injection to eliminate code duplication.
"""

from ..base import create_loader
from .models import Outages

# Configuration constants
DEFAULT_OUTAGES_FILE = "outages.yaml"
DEFAULT_OUTAGES_URL = (
    "https://raw.githubusercontent.com/CCI-MOC/nerc-outages/main/outages.yaml"
)

# Create configured loader using dependency injection
_loader = create_loader(Outages, DEFAULT_OUTAGES_URL, DEFAULT_OUTAGES_FILE)

# Expose the loader functions with proper typing
load_from_url = _loader.load_from_url
load_from_file = _loader.load_from_file

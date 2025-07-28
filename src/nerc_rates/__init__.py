"""
NERC Rates Package

This package provides access to NERC rates and outages data through clean domain APIs.
"""

# Import domain modules to make them accessible
from nerc_rates import rates, outages

# For backward compatibility, also expose rates functions directly
from nerc_rates.rates import load_from_file, load_from_url

__all__ = [
    "rates",
    "outages",
    "load_from_file",  # Backward compatibility
    "load_from_url",   # Backward compatibility
]

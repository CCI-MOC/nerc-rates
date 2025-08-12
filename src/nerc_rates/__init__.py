from . import rates_loader, outages_loader

# For url compatibility, we can also expose the rates functions directly
from .rates_loader import load_from_file, load_from_url

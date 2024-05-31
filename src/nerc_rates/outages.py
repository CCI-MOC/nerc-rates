import requests
import yaml

from .models_outages import Outages

DEFAULT_OUTAGES_FILE = "outages.yaml"
DEFAULT_OUTAGES_URL = (
    "https://raw.githubusercontent.com/CCI-MOC/nerc-outages/main/outages.yaml"
)


def load_from_url(url: str | None = None) -> Outages:
    if url is None:
        url = DEFAULT_OUTAGES_URL

    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    config = yaml.safe_load(r.content.decode("utf-8"))
    return Outages.model_validate(config)


def load_from_file(path: str | None = None) -> Outages:
    if path is None:
        path = DEFAULT_OUTAGES_FILE

    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return Outages.model_validate(config)

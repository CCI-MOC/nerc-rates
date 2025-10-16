import requests
import yaml

from .models.rates_model import Rates

DEFAULT_RATES_FILE = "rates.yaml"
DEFAULT_RATES_URL = (
    "https://raw.githubusercontent.com/CCI-MOC/nerc-rates/main/rates.yaml"
)


def load_from_url(url: str | None = None) -> Rates:
    if url is None:
        url = DEFAULT_RATES_URL

    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    config = yaml.safe_load(r.content.decode("utf-8"))
    return Rates.model_validate(config)


def load_from_file(path: str | None = None) -> Rates:
    if path is None:
        path = DEFAULT_RATES_FILE

    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return Rates.model_validate(config)

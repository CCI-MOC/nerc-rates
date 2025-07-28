"""
Generic Data Loader for NERC

This module provides a generic loader that can load and validate data from URLs or files
for any Pydantic model type, eliminating duplication across domains.
"""

from typing import TypeVar, Type, Optional, Generic
import requests
import yaml
import pydantic

# Generic type variable for any Pydantic model
T = TypeVar('T', bound=pydantic.BaseModel)


class DataLoader(Generic[T]):
    """
    Generic data loader that can load and validate data for any Pydantic model.

    This uses dependency injection to configure the loader with:
    - Model class to validate against
    - Default URL to load from
    - Default file path to load from
    """

    def __init__(
        self,
        model_class: Type[T],
        default_url: str,
        default_file: str
    ):
        """
        Initialize the loader with injected dependencies.

        Args:
            model_class: Pydantic model class to validate data against
            default_url: Default URL to load data from
            default_file: Default file path to load data from
        """
        self.model_class = model_class
        self.default_url = default_url
        self.default_file = default_file

    def load_from_url(self, url: Optional[str] = None) -> T:
        """
        Load and validate data from a URL.

        Args:
            url: URL to load data from. If None, uses the default URL.

        Returns:
            Validated instance of the model class

        Raises:
            requests.RequestException: If the URL cannot be fetched
            yaml.YAMLError: If the YAML cannot be parsed
            pydantic.ValidationError: If the data doesn't match the expected schema
        """
        if url is None:
            url = self.default_url

        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
        config = yaml.safe_load(r.content.decode("utf-8"))
        return self.model_class.model_validate(config)

    def load_from_file(self, path: Optional[str] = None) -> T:
        """
        Load and validate data from a local file.

        Args:
            path: Path to the file. If None, uses the default file path.

        Returns:
            Validated instance of the model class

        Raises:
            FileNotFoundError: If the file doesn't exist
            yaml.YAMLError: If the YAML cannot be parsed
            pydantic.ValidationError: If the data doesn't match the expected schema
        """
        if path is None:
            path = self.default_file

        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return self.model_class.model_validate(config)


def create_loader(model_class: Type[T], default_url: str, default_file: str) -> DataLoader[T]:
    """
    Factory function to create a configured DataLoader instance.

    Args:
        model_class: Pydantic model class to validate data against
        default_url: Default URL to load data from
        default_file: Default file path to load data from

    Returns:
        Configured DataLoader instance
    """
    return DataLoader(model_class, default_url, default_file)

"""
NERC Rates Data Models

This module defines Pydantic models for validating and working with:
- Rates: Historical pricing data with time-based lookups
"""

from typing import Self
from typing import Annotated
from enum import StrEnum
from decimal import Decimal

import datetime
import pydantic

from ..base import Base, parse_date


DateField = Annotated[datetime.date, pydantic.BeforeValidator(parse_date)]


class RateValue(Base):
    """
    Represents a single rate value with its effective date range.

    Attributes:
        value: The rate value as a string (type depends on parent RateItem)
        date_from: Start date when this rate becomes effective
        date_until: End date when this rate expires (None means no expiration)
    """
    value: str
    date_from: Annotated[DateField, pydantic.Field(alias="from")]
    date_until: Annotated[DateField, pydantic.Field(alias="until", default=None)]

    @pydantic.model_validator(mode="after")
    @classmethod
    def validate_date_range(cls, data):
        """Ensure date_until is after date_from when both are present."""
        if data.date_until and data.date_until < data.date_from:
            raise ValueError("date_until must be after date_from")
        return data


class RateType(StrEnum):
    """Supported data types for rate values."""
    STR = "str"
    DECIMAL = "Decimal"
    BOOL = "bool"


# Centralized type mapping to avoid duplication
RATE_TYPE_MAPPING = {
    RateType.STR: str,
    RateType.BOOL: bool,
    RateType.DECIMAL: Decimal
}


class RateItem(Base):
    """
    Represents a named rate with historical values over time.

    Attributes:
        name: Unique identifier for this rate (e.g., "CPU SU Rate")
        type: Data type of the rate values (str, Decimal, bool)
        history: List of rate values with their effective date ranges

    Example:
        RateItem(
            name="CPU SU Rate",
            type="Decimal",
            history=[
                {"value": "0.013", "from": "2023-06", "until": "2024-06"},
                {"value": "0.15", "from": "2024-07"}
            ]
        )
    """
    name: str
    type: RateType
    history: list[RateValue]

    @pydantic.model_validator(mode="after")
    @classmethod
    def validate_no_overlap(cls, data):
        """Ensure no overlapping date ranges in the history."""
        # Sort by start date for easier comparison
        sorted_history = sorted(data.history, key=lambda x: x.date_from)

        for i in range(len(sorted_history) - 1):
            current = sorted_history[i]
            next_item = sorted_history[i + 1]

            # Check if current item's end overlaps with next item's start
            current_end = current.date_until or datetime.date.max
            if current_end >= next_item.date_from:
                raise ValueError("date ranges overlap")

        return data

    @pydantic.model_validator(mode="after")
    @classmethod
    def validate_rate_type(cls, data):
        """Validate that all rate values can be converted to the specified type."""
        rate_type = RATE_TYPE_MAPPING.get(data.type)
        for x in data.history:
            if rate_type == Decimal:
                try:
                    Decimal(x.value)
                except Exception:
                    raise ValueError(f"{x} is not valid Decimal")
            elif rate_type == bool:
                if x.value.lower() not in ["true", "false"]:
                    raise ValueError(f"Bool field must be a string of either True or False, got {x.value}")
        return data


def check_for_duplicates(items):
    """
    Validate that no duplicate rate names exist in the list.

    Args:
        items: List of rate item dictionaries

    Returns:
        Dictionary mapping rate names to rate items

    Raises:
        ValueError: If duplicate names are found
    """
    data = {}
    for item in items:
        if item["name"] in data:
            raise ValueError(f"found duplicate name \"{item['name']}\" in list")
        data[item["name"]] = item
    return data


# Input: list[dict] -> Output: dict[str, RateItem] (via check_for_duplicates validator)
RateItemDict = Annotated[
    dict[str, RateItem],
    pydantic.BeforeValidator(check_for_duplicates),
]


class Rates(pydantic.RootModel):
    """
    Root model for managing all rate items with time-based lookups.

    This model provides the main interface for querying rates by name and date.
    It ensures data integrity and provides type-safe access to rate values.

    Example:
        rates = Rates.model_validate(yaml_data)
        cpu_rate = rates.get_value_at("CPU SU Rate", "2024-01", Decimal)
    """
    root: RateItemDict

    def __getitem__(self, item: str) -> RateItem:
        """Allow dictionary-style access to rate items."""
        return self.root[item]

    def _get_rate_item(self, name: str, queried_date: datetime.date | str) -> RateValue:
        """
        Find the rate value effective at the given date.

        Args:
            name: Rate name to look up
            queried_date: Date to query (string or datetime.date)

        Returns:
            RateValue object effective at the queried date

        Raises:
            ValueError: If no rate is found for the given date
        """
        d = parse_date(queried_date)
        for item in self.root[name].history:
            if item.date_from <= d <= (item.date_until or d):
                return item

        raise ValueError(f"No value for {name} for {queried_date}.")

    def get_value_at(self, name: str, queried_date: datetime.date | str, datatype: type) -> str | bool | Decimal:
        """
        Get a typed rate value at a specific date.

        Args:
            name: Rate name to look up
            queried_date: Date to query (string in 'YYYY-MM' format or datetime.date)
            datatype: Expected Python type (str, bool, Decimal)

        Returns:
            Rate value converted to the specified type

        Raises:
            ValueError: If no rate found for the date
            TypeError: If requested type doesn't match the rate's defined type

        Example:
            rate = rates.get_value_at("CPU SU Rate", "2024-01", Decimal)
            # Returns: Decimal('0.013')
        """
        rate_item_obj = self.root.get(name)
        if rate_item_obj is None:
            raise ValueError(f"Rate '{name}' not found")
        rate_value = self._get_rate_item(name, queried_date)
        expected_type = RATE_TYPE_MAPPING.get(rate_item_obj.type)
        if expected_type is None:
            raise ValueError(f"Unknown rate type: {rate_item_obj.type}")
        if datatype != expected_type:
            raise TypeError(
                f'Rate {name} expects datatype {expected_type.__name__}, '
                f'but got {datatype.__name__}.'
            )
        if expected_type is bool:
            return rate_value.value.lower() in ("true", "1")
        if expected_type is Decimal:
            return Decimal(rate_value.value)
        if expected_type is str:
            return str(rate_value.value)
        return rate_value.value

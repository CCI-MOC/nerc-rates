"""
Shared Base Models for NERC

This module provides common base classes and utilities shared across all NERC domains.
"""

import datetime
import pydantic


def parse_time(v: str | datetime.datetime) -> datetime.datetime:
    """
    Parse datetime from ISO format string or pass through datetime object.

    Handles standard ISO datetime formats and converts to UTC timezone.

    Args:
        v: ISO datetime string or datetime object

    Returns:
        datetime.datetime object in UTC timezone

    Example:
        parse_time("2024-05-22T08:00:00Z") -> datetime.datetime(2024, 5, 22, 8, 0, tzinfo=UTC)
    """
    if isinstance(v, str):
        return datetime.datetime.fromisoformat(v).astimezone(datetime.timezone.utc)
    return v


def parse_date(v: str | datetime.date) -> datetime.date:
    """
    Parse date from string format 'YYYY-MM' or pass through datetime.date.

    Args:
        v: Date string in 'YYYY-MM' format or datetime.date object

    Returns:
        datetime.date object

    Example:
        parse_date("2024-01") -> datetime.date(2024, 1, 1)
    """
    if isinstance(v, str):
        return datetime.datetime.strptime(v, "%Y-%m").date()
    return v


class Base(pydantic.BaseModel):
    """Base model with common configuration for all models."""

    model_config = pydantic.ConfigDict(
        extra='forbid',  # Don't allow extra fields
        validate_assignment=True,  # Validate on assignment
    )

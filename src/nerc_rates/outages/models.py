"""
NERC Outages Data Models

This module defines Pydantic models for validating and working with:
- Outages: Planned service interruptions with date range queries
"""

from typing import Self
from typing import Annotated

import datetime
import pydantic

from ..base import Base, parse_time


TimeField = Annotated[datetime.datetime, pydantic.BeforeValidator(parse_time)]


class OutageTimeFrames(Base):
    """
    Represents a specific time period when services are affected by an outage.

    Attributes:
        time_from: Start time of the outage
        time_until: End time of the outage (None means ongoing)
        affected_services: List of service names affected during this timeframe
    """
    time_from: Annotated[TimeField, pydantic.Field(alias="from")]
    time_until: Annotated[TimeField, pydantic.Field(alias="until", default=None)]
    affected_services: list[str]


class OutageItem(Base):
    """
    Represents a planned outage event with multiple possible timeframes.

    Attributes:
        name: Human-readable name of the outage event
        url: URL with more information about the outage
        timeframes: List of time periods when services are affected

    Example:
        OutageItem(
            name="MGHPCC Shutdown 2024",
            url="https://nerc.mghpcc.org/event/...",
            timeframes=[{
                "from": "2024-05-22T08:00:00Z",
                "until": "2024-05-28T23:00:00Z",
                "affected_services": ["NERC OpenStack"]
            }]
        )
    """
    name: str
    url: pydantic.HttpUrl
    timeframes: list[OutageTimeFrames]


class Outages(pydantic.RootModel):
    """
    Root model for managing outage data with date range queries.

    This model provides the main interface for querying outages that occurred
    during specific time periods for specific services.

    Example:
        outages = Outages.model_validate(yaml_data)
        openstack_outages = outages.get_outages_during(
            "2024-05-01", "2024-06-01", "NERC OpenStack"
        )
    """
    root: list[OutageItem]

    def get_outages_during(self, start: str | datetime.datetime, end: str | datetime.datetime, affected_service: str) -> list[tuple[datetime.datetime, datetime.datetime]]:
        """
        Find all outages affecting a service during a time period.

        Args:
            start: Start date/time as ISO string
            end: End date/time as ISO string
            affected_service: Name of the service to check

        Returns:
            List of (start_time, end_time) datetime tuples for outages that overlap
            with the query period and affect the specified service

        Example:
            outages = outages.get_outages_during(
                "2024-05-01", "2024-06-01", "NERC OpenStack"
            )
            # Returns: [(datetime(2024, 5, 22, 8, 0), datetime(2024, 5, 28, 23, 0))]
        """
        start_dt = start if isinstance(start, datetime.datetime) else datetime.datetime.fromisoformat(start).replace(tzinfo=datetime.timezone.utc)
        end_dt = end if isinstance(end, datetime.datetime) else datetime.datetime.fromisoformat(end).replace(tzinfo=datetime.timezone.utc)

        outages = []
        for outage in self.root:
            for o in outage.timeframes:
                if (affected_service in o.affected_services
                        and o.time_from < end_dt and o.time_until > start_dt):
                    outages.append((max(start_dt, o.time_from), min(end_dt, o.time_until)))

        return outages

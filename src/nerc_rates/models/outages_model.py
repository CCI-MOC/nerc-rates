import logging
from datetime import datetime, timezone, timedelta
from typing import Annotated, Self

import pydantic

from .rates_model import Base

logger = logging.getLogger(__name__)


def parse_time(v: str | datetime) -> datetime:
    if isinstance(v, str):
        dt = datetime.fromisoformat(v)
        # Info: timezone is present and not UTC
        if dt.tzinfo is not None and dt.utcoffset() != timedelta(0):
            raise ValueError(
                "Non-UTC timezone detected in outages data; Please convert to UTC or provide a UTC timezone."
            )
        # Error: naive datetimes are not allowed
        if dt.tzinfo is None:
            raise ValueError(
                "Naive datetime without timezone information is not allowed. "
                "Please provide timezone information (e.g., '2024-01-01T12:00:00Z' or '2024-01-01T12:00:00+00:00')"
            )
        return dt.astimezone(timezone.utc)
    return v


TimeField = Annotated[datetime, pydantic.BeforeValidator(parse_time)]


class OutageTimeFrames(Base):
    time_from: Annotated[TimeField, pydantic.Field(alias="from")]
    time_until: Annotated[TimeField, pydantic.Field(alias="until", default=None)]
    affected_services: list[str]

    @pydantic.model_validator(mode="after")
    @classmethod
    def validate_date_range(cls, data: Self):
        if data.time_until and data.time_until < data.time_from:
            raise ValueError("time_until must be after time_from")
        return data

    @pydantic.model_validator(mode="after")
    @classmethod
    def affected_services_no_duplicates(cls, data: Self):
        if len(data.affected_services) != len(set(data.affected_services)):
            raise ValueError("affected_services must be unique")
        return data


class OutageItem(Base):
    url: pydantic.HttpUrl
    timeframes: list[OutageTimeFrames]


def check_for_duplicate_urls(items: list[dict]) -> list[dict]:
    """Validator to ensure URLs are unique across all outages."""
    urls = []
    for item in items:
        url = str(item["url"])
        if url in urls:
            raise ValueError(f'found duplicate url "{url}" in outages list')
        urls.append(url)
    return items


class Outages(pydantic.RootModel):
    root: Annotated[
        list[OutageItem], pydantic.BeforeValidator(check_for_duplicate_urls)
    ]

    def get_outages_during(self, start, end, affected_service):
        start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)

        outages = []
        for outage in self.root:
            for o in outage.timeframes:
                if affected_service in o.affected_services and (
                    start < o.time_from < end
                    or start < o.time_until < end
                    or (o.time_from <= start and end <= o.time_until)
                ):
                    outages.append((max(start, o.time_from), min(end, o.time_until)))

        return outages

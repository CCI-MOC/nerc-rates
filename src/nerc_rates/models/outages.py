from datetime import datetime, timezone, timedelta
from typing import Annotated, Self
from uuid import UUID

import pydantic
import warnings

from .rates import Base


def parse_time(v: str | datetime) -> datetime:
    if isinstance(v, str):
        dt = datetime.fromisoformat(v)
        # Warn if timezone is present and not UTC
        if dt.tzinfo is not None and dt.utcoffset() != timedelta(0):
            warnings.warn(
                "Non-UTC timezone detected in outages data; converting to UTC",
                UserWarning,
                stacklevel=2,
            )
        # Treat naive datetimes as UTC
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
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
    uuid: UUID
    name: str
    url: pydantic.HttpUrl
    timeframes: list[OutageTimeFrames]


class Outages(pydantic.RootModel):
    root: list[OutageItem]

    def get_outages_during(self, start, end, affected_service):
        start = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)

        outages = []
        for outage in self.root:
            for o in outage.timeframes:
                if affected_service in o.affected_services and (
                    start < o.time_from < end or start < o.time_until < end
                ):
                    outages.append((max(start, o.time_from), min(end, o.time_until)))

        return outages

from datetime import datetime, timezone, timedelta
from typing import Annotated

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


class OutageItem(Base):
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

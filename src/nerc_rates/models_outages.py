from datetime import datetime, timezone
from typing import Self
from typing import Annotated
from enum import StrEnum
from decimal import Decimal

import pydantic

from .models import Base


def parse_time(v: str | datetime) -> datetime:
    if isinstance(v, str):
        return datetime.fromisoformat(v).astimezone(timezone.utc)
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
                if (affected_service in o.affected_services
                        and (start < o.time_from < end or start < o.time_until < end)):
                    outages.append((max(start, o.time_from), min(end, o.time_until)))

        return outages

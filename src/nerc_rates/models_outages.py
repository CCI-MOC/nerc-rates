from typing import Annotated
from datetime import datetime, timezone

import pydantic

from .models import Base


class OutageTimeFrames(Base):
    start: datetime
    end: datetime


class OutageItemDict(Base):
    name: str
    information: str
    timeframes: list[OutageTimeFrames]


class Outages(pydantic.RootModel):
    root: list[OutageItemDict]

    def get_outages_during(self, start, end):
        start = datetime.strptime(start, "%Y-%m-%d").astimezone(timezone.utc)
        end = datetime.strptime(end, "%Y-%m-%d").astimezone(timezone.utc)

        outages = []
        for outage in self.root:
            for o in outage.timeframes:
                if start < o.start < end or start < o.end < end:
                    outages.append((max(start, o.start), min(end, o.end)))

        return outages

"""Pydantic schemas — the API contract.

These validate input at the boundary and shape output. Keeping them separate
from ORM models means the wire format can evolve independently of the DB.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LinkCreate(BaseModel):
    """Request body for creating a short link."""

    long_url: HttpUrl
    # Optional vanity code; if omitted the service generates one.
    custom_code: str | None = Field(
        default=None, min_length=3, max_length=16, pattern=r"^[a-zA-Z0-9_-]+$"
    )


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    long_url: str
    short_url: str
    created_at: datetime


class ClickPoint(BaseModel):
    """A single day's click count for the timeseries chart."""

    date: str
    clicks: int


class LinkAnalytics(BaseModel):
    code: str
    total_clicks: int
    top_referrers: list[tuple[str, int]]
    timeseries: list[ClickPoint]

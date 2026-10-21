"""Validation at the HTTP boundary for event ingestion and count queries."""

import json
import re
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z", re.ASCII)
_MAX_PAYLOAD_BYTES = 16 * 1024


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone offset is required")
    return value.astimezone(timezone.utc)


def _date_input(value: object) -> object:
    # Pydantic otherwise accepts Unix timestamps, which are not RFC3339 inputs.
    if not isinstance(value, (str, datetime)):
        # Pydantic 2 does not convert TypeError from a validator into a 422.
        raise ValueError("An RFC3339 datetime with timezone is required")  # noqa: TRY004
    return value


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Annotated[str, Field(min_length=1, max_length=64)]
    type: Annotated[str, Field(min_length=1, max_length=64)]
    external_id: Annotated[str, Field(min_length=1, max_length=128)]
    occurred_at: datetime
    payload: dict[str, JsonValue]

    @field_validator("source", "type")
    @classmethod
    def simple_identifier(cls, value: str) -> str:
        if _IDENTIFIER.fullmatch(value) is None:
            raise ValueError("A simple identifier is required")
        return value

    @field_validator("occurred_at", mode="before")
    @classmethod
    def occurred_at_input(cls, value: object) -> object:
        return _date_input(value)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_utc(cls, value: datetime) -> datetime:
        return _utc(value)

    @field_validator("payload")
    @classmethod
    def payload_size(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        try:
            encoded = json.dumps(
                value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Payload must be JSON") from exc
        if len(encoded) > _MAX_PAYLOAD_BYTES:
            raise ValueError("Payload exceeds 16 KiB")
        return value


class CountsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_: datetime = Field(alias="from")
    to: datetime
    group_by: Literal["type", "source"]

    @field_validator("from_", "to", mode="before")
    @classmethod
    def window_input(cls, value: object) -> object:
        return _date_input(value)

    @field_validator("from_", "to")
    @classmethod
    def window_utc(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def ordered_window(self) -> "CountsQuery":
        if self.from_ >= self.to:
            raise ValueError("The start of the window must be before its end")
        return self

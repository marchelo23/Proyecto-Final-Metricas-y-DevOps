"""Provisional API-key authentication and role-based authorization for the MVP."""

import os
from dataclasses import dataclass
from hmac import compare_digest
from typing import Annotated, Literal

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class Principal:
    role: Literal["producer", "analyst"]


_ALLOWED = frozenset(
    {
        ("producer", "events:create"),
        ("analyst", "events:read"),
        ("analyst", "analysis:read"),
    }
)


def _unauthenticated() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid or missing API key")


def _authenticate(api_key: str | None) -> Principal:
    producer_key = os.environ.get("EVENT_PRODUCER_KEY")
    analyst_key = os.environ.get("EVENT_ANALYST_KEY")

    # Both credentials must exist and be distinct. A partial or ambiguous
    # configuration must never grant access to either role.
    if (
        not producer_key
        or not producer_key.strip()
        or not analyst_key
        or not analyst_key.strip()
        or compare_digest(producer_key, analyst_key)
        or not api_key
        or not api_key.strip()
    ):
        raise _unauthenticated()

    producer_match = compare_digest(api_key, producer_key)
    analyst_match = compare_digest(api_key, analyst_key)
    if producer_match:
        return Principal(role="producer")
    if analyst_match:
        return Principal(role="analyst")
    raise _unauthenticated()


def require_producer(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> Principal:
    """FastAPI dependency for event creation routes."""
    principal = _authenticate(x_api_key)
    if principal.role != "producer":
        raise HTTPException(status_code=403, detail="Forbidden")
    return principal


def require_analyst(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> Principal:
    """FastAPI dependency for event and analysis read routes."""
    principal = _authenticate(x_api_key)
    if principal.role != "analyst":
        raise HTTPException(status_code=403, detail="Forbidden")
    return principal


def ensure_permission(
    principal: Principal,
    action: Literal["events:create", "events:read", "analysis:read"],
) -> None:
    """Enforce an operation's permission in its owning service function."""
    if (principal.role, action) not in _ALLOWED:
        raise HTTPException(status_code=403, detail="Forbidden")

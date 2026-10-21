"""COM-01: acceptance tests against the real HTTP app and isolated PostgreSQL."""

import os
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url

PRODUCER_KEY = "acceptance-producer-only"
ANALYST_KEY = "acceptance-analyst-only"
PRODUCER = {"X-API-Key": PRODUCER_KEY}
ANALYST = {"X-API-Key": ANALYST_KEY}


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("requires a dedicated PostgreSQL TEST_DATABASE_URL")
    parsed = make_url(url)
    if (
        parsed.drivername != "postgresql+psycopg"
        or not parsed.database
        or "test" not in parsed.database.lower()
    ):
        pytest.fail(
            "TEST_DATABASE_URL must use psycopg and name an isolated test database"
        )
    configured = os.environ.get("DATABASE_URL")
    if configured and configured != url:
        pytest.fail("DATABASE_URL must equal TEST_DATABASE_URL for acceptance tests")
    return url


@pytest.fixture(scope="session")
def client(test_database_url: str) -> Iterator[TestClient]:
    # Set these before importing the app: some configurations are read at import.
    with pytest.MonkeyPatch.context() as env:
        env.setenv("DATABASE_URL", test_database_url)
        env.setenv("EVENT_PRODUCER_KEY", PRODUCER_KEY)
        env.setenv("EVENT_ANALYST_KEY", ANALYST_KEY)
        from event_service.config import Settings
        from event_service.main import create_app

        with TestClient(create_app(Settings.from_env())) as http:
            yield http


@pytest.fixture(scope="session")
def cleanup_engine(test_database_url: str) -> Iterator[Engine]:
    engine = create_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def new_source(cleanup_engine: Engine) -> Iterator[Callable[[], str]]:
    owned_sources: list[str] = []

    def allocate() -> str:
        source = f"acc{uuid4().hex}"
        owned_sources.append(source)
        return source

    yield allocate
    # Never truncate the database: remove only rows created by this test.
    with cleanup_engine.begin() as connection:
        for source in owned_sources:
            connection.execute(
                text("DELETE FROM events WHERE source = :source"), {"source": source}
            )


@pytest.fixture
def window() -> tuple[datetime, datetime]:
    # Each test has its own time window, independent of pre-existing test data.
    start = datetime(2040, 1, 1, 12, tzinfo=timezone.utc) + timedelta(
        days=uuid4().int % 36525
    )
    return start, start + timedelta(hours=1)


def _post(
    client: TestClient,
    source: str,
    occurred_at: datetime,
    *,
    external_id: str | None = None,
    event_type: str = "temperature",
    payload: dict[str, object] | None = None,
):
    return client.post(
        "/v1/events",
        headers=PRODUCER,
        json={
            "source": source,
            "external_id": external_id or uuid4().hex,
            "type": event_type,
            "occurred_at": occurred_at.isoformat(),
            "payload": {"value": 23.5} if payload is None else payload,
        },
    )


def _counts(
    client: TestClient,
    start: datetime,
    end: datetime,
    group_by: str = "type",
):
    return client.get(
        "/v1/analysis/counts",
        headers=ANALYST,
        params={"from": start.isoformat(), "to": end.isoformat(), "group_by": group_by},
    )


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def test_ingestion_returns_persisted_event(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    source = new_source()
    start, _ = window
    offset = timezone(timedelta(hours=-4))
    created = _post(
        client,
        source,
        start.astimezone(offset),
        external_id="original-1",
        payload={"value": 23.5},
    )

    assert created.status_code == 201
    event = created.json()
    assert set(event) == {
        "id",
        "source",
        "external_id",
        "type",
        "occurred_at",
        "payload",
        "ingested_at",
    }
    UUID(event["id"])
    assert (event["source"], event["external_id"], event["type"]) == (
        source,
        "original-1",
        "temperature",
    )
    assert event["payload"] == {"value": 23.5}
    assert _utc(event["occurred_at"]) == start
    assert _utc(event["ingested_at"])


def test_analyst_can_retrieve_event_and_missing_id_is_404(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    created = _post(client, new_source(), window[0])
    assert created.status_code == 201
    found = client.get(f"/v1/events/{created.json()['id']}", headers=ANALYST)
    missing = client.get(f"/v1/events/{uuid4()}", headers=ANALYST)

    assert found.status_code == 200
    assert found.json() == created.json()
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"


def test_duplicate_does_not_modify_or_duplicate_first_event(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    source = new_source()
    start, end = window
    original = _post(client, source, start, external_id="same-id", payload={"value": 1})
    duplicate = _post(
        client, source, start, external_id="same-id", payload={"value": 999}
    )

    assert original.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE"
    found = client.get(f"/v1/events/{original.json()['id']}", headers=ANALYST)
    assert found.status_code == 200
    assert found.json() == original.json()
    counted = _counts(client, start, end)
    assert counted.status_code == 200
    assert counted.json()["total"] == 1


def test_external_id_can_repeat_in_another_source(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    first = _post(client, new_source(), window[0], external_id="shared-id")
    second = _post(client, new_source(), window[0], external_id="shared-id")
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_counts_by_type_and_source_are_sorted_and_empty_window_is_zero(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    first, second = new_source(), new_source()
    start, end = window
    for source, event_type in [
        (first, "temperature"),
        (first, "humidity"),
        (second, "temperature"),
    ]:
        assert _post(client, source, start, event_type=event_type).status_code == 201

    by_type = _counts(client, start, end)
    by_source = _counts(client, start, end, "source")
    empty = _counts(client, end + timedelta(days=1), end + timedelta(days=2))

    assert by_type.status_code == by_source.status_code == empty.status_code == 200
    assert by_type.json()["total"] == 3
    assert by_type.json()["group_by"] == "type"
    assert _utc(by_type.json()["window"]["from"]) == start
    assert _utc(by_type.json()["window"]["to"]) == end
    assert by_type.json()["buckets"] == [
        {"key": "humidity", "count": 1},
        {"key": "temperature", "count": 2},
    ]
    assert by_source.json()["total"] == 3
    assert by_source.json()["group_by"] == "source"
    assert by_source.json()["buckets"] == [
        {"key": source, "count": count}
        for source, count in sorted([(first, 2), (second, 1)])
    ]
    assert empty.json()["total"] == 0
    assert empty.json()["buckets"] == []


def test_counts_use_half_open_utc_window(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    source = new_source()
    start, end = window
    for instant in [
        start - timedelta(microseconds=1),
        start.astimezone(timezone(timedelta(hours=-4))),
        end - timedelta(microseconds=1),
        end,
    ]:
        assert _post(client, source, instant).status_code == 201

    # Equivalent non-UTC query offsets must normalize to the same UTC window.
    offset = timezone(timedelta(hours=-4))
    result = _counts(client, start.astimezone(offset), end.astimezone(offset))
    assert result.status_code == 200
    body = result.json()
    assert body["total"] == 2
    assert body["buckets"] == [{"key": "temperature", "count": 2}]
    assert _utc(body["window"]["from"]) == start
    assert _utc(body["window"]["to"]) == end


def test_protected_routes_require_correct_role(
    client: TestClient, new_source: Callable[[], str], window: tuple[datetime, datetime]
) -> None:
    source = new_source()
    start, end = window
    body = {
        "source": source,
        "external_id": uuid4().hex,
        "type": "temperature",
        "occurred_at": start.isoformat(),
        "payload": {},
    }
    assert client.post("/v1/events", json=body).status_code == 401
    assert client.post("/v1/events", headers=ANALYST, json=body).status_code == 403
    created = client.post("/v1/events", headers=PRODUCER, json=body)
    assert created.status_code == 201
    event_url = f"/v1/events/{created.json()['id']}"
    counts_params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "group_by": "type",
    }
    assert client.get(event_url).status_code == 401
    assert client.get(event_url, headers=PRODUCER).status_code == 403
    assert client.get(event_url, headers=ANALYST).status_code == 200
    assert client.get("/v1/analysis/counts", params=counts_params).status_code == 401
    assert (
        client.get(
            "/v1/analysis/counts", headers=PRODUCER, params=counts_params
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/v1/analysis/counts", headers=ANALYST, params=counts_params
        ).status_code
        == 200
    )


def test_service_rechecks_permission_before_repository_access(
    client: TestClient, window: tuple[datetime, datetime]
) -> None:
    from event_service.auth import Principal
    from event_service.schemas import CountsQuery, EventCreate

    from event_service.service import count_events, create_event, get_event

    class NoAccessRepository:
        def create(self, **kwargs):
            raise AssertionError("unauthorized create touched repository")

        def get(self, event_id):
            raise AssertionError("unauthorized get touched repository")

        def counts(self, start, end, group_by):
            raise AssertionError("unauthorized counts touched repository")

    start, end = window
    event = EventCreate(
        source="acceptance",
        external_id="id",
        type="temperature",
        occurred_at=start,
        payload={},
    )
    query = CountsQuery.model_validate(
        {"from": start.isoformat(), "to": end.isoformat(), "group_by": "type"}
    )
    repository = NoAccessRepository()
    for operation in (
        lambda: create_event(event, Principal(role="analyst"), repository),
        lambda: get_event(uuid4(), Principal(role="producer"), repository),
        lambda: count_events(query, Principal(role="producer"), repository),
    ):
        with pytest.raises(HTTPException) as error:
            operation()
        assert error.value.status_code == 403


def test_invalid_count_window_is_rejected(
    client: TestClient, window: tuple[datetime, datetime]
) -> None:
    start, _ = window
    result = _counts(client, start, start)
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "INVALID_INPUT"


@pytest.mark.parametrize(
    "invalid_field",
    [
        {"source": ""},
        {"source": "bad source"},
        {"source": "s" * 65},
        {"type": ""},
        {"type": "bad type"},
        {"type": "t" * 65},
        {"external_id": ""},
        {"external_id": "e" * 129},
        {"occurred_at": "2026-10-21T12:00:00"},
        {"payload": [1, 2]},
    ],
)
def test_ingestion_rejects_invalid_fields(
    client: TestClient,
    new_source: Callable[[], str],
    window: tuple[datetime, datetime],
    invalid_field: dict[str, object],
) -> None:
    body = {
        "source": new_source(),
        "external_id": uuid4().hex,
        "type": "temperature",
        "occurred_at": window[0].isoformat(),
        "payload": {"value": 1},
        **invalid_field,
    }
    response = client.post("/v1/events", headers=PRODUCER, json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


@pytest.mark.parametrize(
    "invalid_query",
    [
        {"from": "2026-10-21T12:00:00"},
        {"to": "2026-10-21T13:00:00"},
        {"group_by": "payload"},
    ],
)
def test_counts_reject_invalid_query(
    client: TestClient,
    window: tuple[datetime, datetime],
    invalid_query: dict[str, str],
) -> None:
    start, end = window
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "group_by": "type",
        **invalid_query,
    }
    response = client.get("/v1/analysis/counts", headers=ANALYST, params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_health_endpoints_are_public(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200

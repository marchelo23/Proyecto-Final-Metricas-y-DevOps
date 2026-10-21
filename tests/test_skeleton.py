"""Pruebas de la base, aisladas de cualquier PostgreSQL real."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from event_service.config import Settings
from event_service.main import create_app


def test_live_does_not_depend_on_database() -> None:
    with TestClient(create_app(Settings.from_env({}))) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_without_database_is_503_and_safe() -> None:
    with TestClient(create_app(Settings.from_env({}))) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert response.json()["error"]["request_id"]
    assert "DATABASE_URL" not in response.text


def test_ready_checks_select_one_when_database_is_configured(monkeypatch) -> None:
    executed = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, statement):
            executed.append(str(statement))

    class Engine:
        def connect(self):
            return Connection()

    def fake_create_engine(*_args, **_kwargs):
        return Engine()

    monkeypatch.setattr("event_service.main.create_engine", fake_create_engine)
    settings = Settings.from_env({"DATABASE_URL": "postgresql+psycopg://user:secret@db/events"})
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert executed == ["SELECT 1"]


def test_ready_masks_database_errors(monkeypatch) -> None:
    secret = "postgresql+psycopg://user:secret@db/events"

    class Engine:
        def connect(self):
            raise SQLAlchemyError(secret)

    monkeypatch.setattr("event_service.main.create_engine", lambda *_args, **_kwargs: Engine())
    with TestClient(create_app(Settings.from_env({"DATABASE_URL": secret}))) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert secret not in response.text


def test_live_survives_invalid_database_url_and_ready_is_503() -> None:
    with TestClient(create_app(Settings.from_env({"DATABASE_URL": "not-a-url"}))) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

    assert live.status_code == 200
    assert ready.status_code == 503
    assert "not-a-url" not in ready.text


def test_ready_rejects_non_postgres_url() -> None:
    with TestClient(create_app(Settings.from_env({"DATABASE_URL": "sqlite:///:memory:"}))) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503


def test_settings_have_no_secret_defaults() -> None:
    settings = Settings.from_env({})

    assert settings.database_url is None
    assert settings.event_producer_key is None
    assert settings.event_analyst_key is None


def test_settings_read_distinct_keys_without_echoing_them() -> None:
    settings = Settings.from_env(
        {
            "EVENT_PRODUCER_KEY": "producer-value",
            "EVENT_ANALYST_KEY": "analyst-value",
        }
    )

    assert settings.event_producer_key.get_secret_value() == "producer-value"
    assert settings.event_analyst_key.get_secret_value() == "analyst-value"
    assert "producer-value" not in repr(settings)
    assert "analyst-value" not in repr(settings)

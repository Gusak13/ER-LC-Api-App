import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SERVER_KEY", "test-server-key")
    monkeypatch.setenv("COMMAND_ALLOWLIST", "h,m")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_renders_development_page() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "ER:LC Control Panel" in response.text


def test_server_endpoint_exposes_only_safe_summary() -> None:
    class FakeClient:
        def get_server(self) -> dict:
            return {
                "Name": "Test Server",
                "CurrentPlayers": 2,
                "MaxPlayers": 40,
                "AccVerifiedReq": "Email",
                "TeamBalance": True,
                "JoinKey": "must-not-leak",
            }

    with TestClient(app) as client:
        app.state.erlc_client = FakeClient()
        response = client.get("/api/server")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Test Server",
        "current_players": 2,
        "max_players": 40,
        "account_verification": "Email",
        "team_balance": True,
    }

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


def test_default_command_allowlist_enables_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COMMAND_ALLOWLIST")
    get_settings.cache_clear()

    assert get_settings().command_allowlist == frozenset({"*"})


def test_index_renders_development_page() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Server Control" in response.text
    assert 'id="command-form"' in response.text


def test_players_page_renders_players_view() -> None:
    with TestClient(app) as client:
        response = client.get("/players")

    assert response.status_code == 200
    assert 'id="players-list"' in response.text


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


def test_players_endpoint_returns_player_summaries() -> None:
    class FakeClient:
        def get_players(self) -> dict:
            return {
                "Players": [
                    {
                        "Player": "DeputyNova:123456789",
                        "Team": "Sheriff",
                        "Permission": "Admin",
                        "Callsign": "S-12",
                        "WantedStars": 0,
                    }
                ]
            }

    with TestClient(app) as client:
        app.state.erlc_client = FakeClient()
        response = client.get("/api/players")

    assert response.status_code == 200
    assert response.json() == {
        "players": [
            {
                "username": "DeputyNova",
                "roblox_id": 123456789,
                "team": "Sheriff",
                "permission": "Admin",
                "callsign": "S-12",
                "wanted_stars": 0,
            }
        ]
    }

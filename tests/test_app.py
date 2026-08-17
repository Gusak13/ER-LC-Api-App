import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

TEST_ORIGIN = {"Origin": "http://testserver"}


class AuthenticatedFakeClient:
    def __init__(self, target=None) -> None:
        self.target = target

    def get_server(self) -> dict:
        if self.target is not None and hasattr(self.target, "get_server"):
            return self.target.get_server()
        return {
            "Name": "Test Server",
            "CurrentPlayers": 0,
            "MaxPlayers": 40,
            "AccVerifiedReq": "None",
            "TeamBalance": False,
        }

    def close(self) -> None:
        pass

    def __getattr__(self, name: str):
        if self.target is None:
            raise AttributeError(name)
        return getattr(self.target, name)


def login(client: TestClient, target=None) -> None:
    app.state.client_factory = lambda _api_key: AuthenticatedFakeClient(target)
    response = client.post(
        "/api/auth/login",
        json={"api_key": "test-api-key"},
        headers=TEST_ORIGIN,
    )
    assert response.status_code == 200


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
        login(client)
        response = client.get("/")

    assert response.status_code == 200
    assert "Server Control" in response.text
    assert 'id="command-form"' in response.text


def test_players_page_renders_players_view() -> None:
    with TestClient(app) as client:
        login(client)
        response = client.get("/players")

    assert response.status_code == 200
    assert 'id="players-list"' in response.text
    assert 'id="player-search"' in response.text
    assert 'id="team-filter"' in response.text


def test_navigation_pages_render_their_expected_controls() -> None:
    with TestClient(app) as client:
        login(client)
        commands = client.get("/commands")
        activity = client.get("/activity")
        map_page = client.get("/map")

    assert commands.status_code == 200
    assert 'id="command-logs-list"' in commands.text
    assert activity.status_code == 200
    assert 'id="activity-filter"' in activity.text
    assert 'id="bans-list"' in activity.text
    assert map_page.status_code == 200
    assert 'id="live-map"' in map_page.text
    assert 'id="map-style"' in map_page.text
    assert 'id="map-canvas"' in map_page.text
    assert 'id="map-zoom-in"' in map_page.text


def test_local_map_assets_are_available() -> None:
    with TestClient(app) as client:
        fall_map = client.get("/maps/fall_postals.png")
        snow_map = client.get("/maps/snow_postals.png")

    assert fall_map.status_code == 200
    assert fall_map.headers["content-type"] == "image/png"
    assert snow_map.status_code == 200
    assert snow_map.headers["content-type"] == "image/png"


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
        login(client, FakeClient())
        response = client.get("/api/server")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Test Server",
        "current_players": 2,
        "max_players": 40,
        "account_verification": "Email",
        "team_balance": True,
    }


def test_dashboard_endpoint_exposes_operational_snapshot() -> None:
    class FakeClient:
        def get_dashboard(self) -> dict:
            return {
                "Name": "Test Server",
                "CurrentPlayers": 2,
                "MaxPlayers": 40,
                "AccVerifiedReq": "Email",
                "TeamBalance": True,
                "JoinKey": "must-not-leak",
                "Players": [
                    {
                        "Player": "AdminNova:123",
                        "Team": "Police",
                        "Permission": "Admin",
                        "Callsign": "P-12",
                        "WantedStars": 0,
                    },
                    {
                        "Player": "CivilianRiver:456",
                        "Team": "Civilian",
                        "Permission": "Normal",
                        "WantedStars": 3,
                    },
                ],
                "Staff": {
                    "CoOwners": [1],
                    "Admins": {"123": "AdminNova"},
                    "Mods": {},
                    "Helpers": {},
                },
                "Queue": [789],
                "EmergencyCalls": [
                    {
                        "CallNumber": 4,
                        "Caller": "CivilianRiver:456",
                        "Team": "Police",
                        "Description": "Traffic stop",
                        "PositionDescriptor": "Near postal 123",
                        "Players": ["AdminNova:123"],
                    }
                ],
                "Vehicles": [
                    {"Name": "Police Cruiser", "Owner": "AdminNova:123", "Plate": "P12"}
                ],
            }

    with TestClient(app) as client:
        login(client, FakeClient())
        response = client.get("/api/server/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Test Server"
    assert body["team_counts"] == {"Police": 1, "Civilian": 1}
    assert body["staff_online"] == [
        {"username": "AdminNova", "role": "Admin", "team": "Police", "callsign": "P-12"}
    ]
    assert body["wanted_players"] == [
        {"username": "CivilianRiver", "wanted_stars": 3, "team": "Civilian"}
    ]
    assert body["queue"] == ["789"]
    assert body["emergency_calls"][0]["description"] == "Traffic stop"
    assert body["vehicles"] == [
        {"name": "Police Cruiser", "owner": "AdminNova", "plate": "P12"}
    ]
    assert "must-not-leak" not in response.text


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
                        "Location": {
                            "LocationX": 1084.965,
                            "LocationZ": 2302.28,
                            "PostalCode": "218",
                            "StreetName": "Park Street",
                            "BuildingNumber": "2083",
                        },
                    }
                ]
            }

    with TestClient(app) as client:
        login(client, FakeClient())
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
                "location": {
                    "x": 1084.965,
                    "z": 2302.28,
                    "postal_code": "218",
                    "street_name": "Park Street",
                    "building_number": "2083",
                },
            }
        ]
    }


def test_activity_endpoint_returns_logs_and_current_bans() -> None:
    class FakeClient:
        def get_activity(self) -> dict:
            return {
                "JoinLogs": [
                    {"Join": True, "Timestamp": 1704614400, "Player": "Nova:123"}
                ],
                "KillLogs": [
                    {
                        "Killer": "Nova:123",
                        "Killed": "River:456",
                        "Timestamp": 1704614401,
                    }
                ],
                "CommandLogs": [
                    {
                        "Player": "Admin:1",
                        "Command": ":kick Nova",
                        "Timestamp": 1704614402,
                    }
                ],
                "ModCalls": [
                    {"Caller": "River:456", "Moderator": None, "Timestamp": 1704614403}
                ],
            }

        def get_bans(self) -> list:
            return [{"PlayerId": "BannedPlayer"}]

    with TestClient(app) as client:
        login(client, FakeClient())
        response = client.get("/api/activity")

    assert response.status_code == 200
    assert response.json() == {
        "join_logs": [{"player": "Nova:123", "joined": True, "timestamp": 1704614400}],
        "kill_logs": [
            {"killer": "Nova:123", "killed": "River:456", "timestamp": 1704614401}
        ],
        "command_logs": [
            {"player": "Admin:1", "command": ":kick Nova", "timestamp": 1704614402}
        ],
        "mod_calls": [
            {"caller": "River:456", "moderator": None, "timestamp": 1704614403}
        ],
        "bans": [{"player": "BannedPlayer"}],
    }

from fastapi.testclient import TestClient

from app.auth import LoginRateLimiter, SessionStore
from app.client import ERLCAPIError
from app.main import app

TEST_ORIGIN = {"Origin": "http://testserver"}


class FakeClient:
    def __init__(self, api_key: str, *, error: ERLCAPIError | None = None) -> None:
        self.api_key = api_key
        self.error = error
        self.closed = False

    def get_server(self) -> dict:
        if self.error is not None:
            raise self.error
        return {"Name": "Liberty County Test"}

    def close(self) -> None:
        self.closed = True


def test_protected_pages_redirect_to_login() -> None:
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)
        api_response = client.get("/api/server")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert api_response.status_code == 401


def test_login_page_uses_its_own_minimal_styles() -> None:
    with TestClient(app) as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert "/static/css/login.css" in response.text
    assert "/static/css/styles.css" not in response.text
    assert "Private by design" not in response.text
    assert "Private server control" not in response.text
    assert "Connect your server" not in response.text


def test_valid_key_creates_httponly_session_without_exposing_key() -> None:
    created: list[FakeClient] = []

    def factory(api_key: str) -> FakeClient:
        fake = FakeClient(api_key)
        created.append(fake)
        return fake

    with TestClient(app) as client:
        app.state.client_factory = factory
        response = client.post(
            "/api/auth/login",
            json={"api_key": "private-test-key"},
            headers=TEST_ORIGIN,
        )
        page = client.get("/")

    cookie = response.headers["set-cookie"]
    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "server_name": "Liberty County Test",
    }
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/" in cookie
    assert "private-test-key" not in cookie
    assert "private-test-key" not in response.text
    assert page.status_code == 200
    assert "Liberty County Test" in page.text
    assert created[0].api_key == "private-test-key"


def test_invalid_key_returns_generic_error_and_closes_client() -> None:
    fake = FakeClient(
        "invalid-secret-key",
        error=ERLCAPIError(
            "Detailed upstream credential error",
            status_code=403,
            api_code=2002,
        ),
    )
    with TestClient(app) as client:
        app.state.client_factory = lambda _api_key: fake
        response = client.post(
            "/api/auth/login",
            json={"api_key": "invalid-secret-key"},
            headers=TEST_ORIGIN,
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "That API key could not be verified."}
    assert "invalid-secret-key" not in response.text
    assert "Detailed upstream" not in response.text
    assert fake.closed is True


def test_login_rejects_cross_origin_requests() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"api_key": "private-test-key"},
            headers={"Origin": "https://attacker.example"},
        )

    assert response.status_code == 403


def test_invalid_login_payload_does_not_echo_key() -> None:
    short_key = "secret"
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"api_key": short_key},
            headers=TEST_ORIGIN,
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Enter a valid API key."}
    assert short_key not in response.text


def test_logout_removes_session_and_closes_client() -> None:
    fake = FakeClient("private-test-key")
    with TestClient(app) as client:
        app.state.client_factory = lambda _api_key: fake
        login = client.post(
            "/api/auth/login",
            json={"api_key": "private-test-key"},
            headers=TEST_ORIGIN,
        )
        logout = client.post("/api/auth/logout", headers=TEST_ORIGIN)
        protected = client.get("/api/server")

    assert login.status_code == 200
    assert logout.status_code == 204
    assert protected.status_code == 401
    assert fake.closed is True


def test_command_rejects_cross_origin_request() -> None:
    class CommandClient(FakeClient):
        def run_command(self, command: str) -> dict[str, str]:
            return {"message": command}

    fake = CommandClient("private-test-key")
    with TestClient(app) as client:
        app.state.client_factory = lambda _api_key: fake
        client.post(
            "/api/auth/login",
            json={"api_key": "private-test-key"},
            headers=TEST_ORIGIN,
        )
        response = client.post(
            "/api/commands",
            json={"command": ":h Hello"},
            headers={"Origin": "https://attacker.example"},
        )

    assert response.status_code == 403


def test_session_store_expires_idle_session_and_closes_client() -> None:
    now = [100.0]
    fake = FakeClient("private-test-key")
    store = SessionStore(
        idle_seconds=10,
        absolute_seconds=100,
        clock=lambda: now[0],
    )
    token = store.create(fake, "Test Server")

    assert store.get(token) is not None
    now[0] += 11

    assert store.get(token) is None
    assert fake.closed is True


def test_rate_limiter_blocks_after_five_failures() -> None:
    now = [100.0]
    limiter = LoginRateLimiter(clock=lambda: now[0])
    for _ in range(5):
        limiter.record_failure("client")

    assert limiter.retry_after("client") == 900
    now[0] += 901
    assert limiter.retry_after("client") is None

import pytest

from app.client import ERLCAPIError, ERLCClient


class FakeResponse:
    def __init__(self, status_code: int, body: dict) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> dict:
        return self._body


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.headers: dict[str, str] = {}
        self.response = response
        self.last_request: tuple | None = None

    def request(self, method: str, url: str, **kwargs) -> FakeResponse:
        self.last_request = (method, url, kwargs)
        return self.response


def test_get_server_builds_v2_request() -> None:
    session = FakeSession(FakeResponse(200, {"Name": "Test"}))
    client = ERLCClient("secret", session=session)

    assert client.get_server() == {"Name": "Test"}
    assert session.last_request == (
        "GET",
        "https://api.erlc.gg/v2/server",
        {"timeout": 20},
    )
    assert session.headers["server-key"] == "secret"


def test_run_command_posts_json_once() -> None:
    session = FakeSession(FakeResponse(200, {"message": "Success"}))
    client = ERLCClient("secret", session=session)

    assert client.run_command(":h Hello") == {"message": "Success"}
    assert session.last_request == (
        "POST",
        "https://api.erlc.gg/v1/server/command",
        {"timeout": 20, "json": {"command": ":h Hello"}},
    )


def test_api_error_preserves_status_and_code() -> None:
    session = FakeSession(
        FakeResponse(403, {"code": 2002, "message": "Invalid server key"})
    )
    client = ERLCClient("secret", session=session)

    with pytest.raises(ERLCAPIError) as caught:
        client.get_server()

    assert caught.value.status_code == 403
    assert caught.value.api_code == 2002
    assert str(caught.value) == "Invalid server key"

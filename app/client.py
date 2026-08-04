from typing import Any

import requests


class ERLCAPIError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        api_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.api_code = api_code


class ERLCClient:
    BASE_URL = "https://api.erlc.gg"

    def __init__(
        self,
        server_key: str,
        *,
        session: requests.Session | None = None,
    ) -> None:
        server_key = server_key.strip()
        if not server_key:
            raise ValueError("server_key cannot be empty")

        self._session = session or requests.Session()
        self._owns_session = session is None
        self._session.headers.update(
            {
                "Accept": "application/json",
                "server-key": server_key,
                "User-Agent": "ERLC-Control-Panel/0.1",
            }
        )

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        try:
            response = self._session.request(
                method,
                f"{self.BASE_URL}{path}",
                timeout=20,
                **kwargs,
            )
        except requests.RequestException as error:
            raise ERLCAPIError(f"ER:LC request failed: {error}") from error

        try:
            body = response.json()
        except requests.JSONDecodeError as error:
            raise ERLCAPIError(
                f"ER:LC returned HTTP {response.status_code} with invalid JSON",
                status_code=response.status_code,
            ) from error

        if response.status_code != 200:
            if isinstance(body, dict):
                message = (
                    body.get("message") or body.get("detail") or "Unknown API error"
                )
                api_code = body.get("code") or body.get("error_code")
            else:
                message = "Unknown API error"
                api_code = None
            raise ERLCAPIError(
                str(message),
                status_code=response.status_code,
                api_code=api_code,
            )

        if not isinstance(body, (dict, list)):
            raise ERLCAPIError("ER:LC returned an unexpected response shape")
        return body

    def get_server(self) -> dict[str, Any]:
        response = self._request("GET", "/v2/server")
        if not isinstance(response, dict):
            raise ERLCAPIError("ER:LC returned an unexpected server response")
        return response

    def get_players(self) -> dict[str, Any]:
        response = self._request(
            "GET",
            "/v2/server",
            params={"Players": "true"},
        )
        if not isinstance(response, dict):
            raise ERLCAPIError("ER:LC returned an unexpected players response")
        return response

    def get_dashboard(self) -> dict[str, Any]:
        response = self._request(
            "GET",
            "/v2/server",
            params={
                "Players": "true",
                "Staff": "true",
                "Queue": "true",
                "EmergencyCalls": "true",
                "Vehicles": "true",
            },
        )
        if not isinstance(response, dict):
            raise ERLCAPIError("ER:LC returned an unexpected dashboard response")
        return response

    def get_activity(self) -> dict[str, Any]:
        response = self._request(
            "GET",
            "/v2/server",
            params={
                "JoinLogs": "true",
                "KillLogs": "true",
                "CommandLogs": "true",
                "ModCalls": "true",
            },
        )
        if not isinstance(response, dict):
            raise ERLCAPIError("ER:LC returned an unexpected activity response")
        return response

    def get_bans(self) -> dict[str, Any] | list[Any]:
        return self._request("GET", "/v1/server/bans")

    def run_command(self, command: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/v1/server/command",
            json={"command": command},
        )
        if not isinstance(response, dict):
            raise ERLCAPIError("ER:LC returned an unexpected command response")
        return response

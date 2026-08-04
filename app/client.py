import os
from pathlib import Path
from typing import Any

import requests


class ERLCAPIError(RuntimeError):
    pass


def _load_env(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name.strip(), value)


class ERLCClient:
    BASE_URL = "https://api.erlc.gg"

    def __init__(self, server_key: str | None = None) -> None:
        _load_env(Path(__file__).resolve().parents[1] / ".env")
        self.server_key = (server_key or os.environ.get("SERVER_KEY", "")).strip()
        if not self.server_key:
            raise ERLCAPIError("SERVER_KEY is missing from .env")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "server-key": self.server_key,
                "User-Agent": "ERLC-Api-App/1.0",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.session.request(
                method,
                f"{self.BASE_URL}{path}",
                timeout=20,
                **kwargs,
            )
        except requests.RequestException as error:
            raise ERLCAPIError(f"API request failed: {error}") from error

        try:
            body = response.json()
        except requests.JSONDecodeError as error:
            raise ERLCAPIError(
                f"API returned HTTP {response.status_code} with invalid JSON"
            ) from error

        if response.status_code != 200:
            message = body.get("message") or body.get("detail") or "Unknown API error"
            code = body.get("code") or body.get("error_code")
            code_text = f" (code {code})" if code is not None else ""
            raise ERLCAPIError(
                f"API returned HTTP {response.status_code}{code_text}: {message}"
            )

        return body

    def get_server(self) -> dict[str, Any]:
        return self._request("GET", "/v2/server")

    def run_command(self, command: str) -> dict[str, Any]:
        command = command.strip()
        if not command:
            raise ValueError("Command cannot be empty")
        if not command.startswith(":"):
            raise ValueError("ER:LC commands must begin with ':'")

        return self._request(
            "POST",
            "/v1/server/command",
            json={"command": command},
        )
import os
import sys
from pathlib import Path

import requests


def load_env(path: Path) -> None:
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


def main() -> int:
    load_env(Path(__file__).with_name(".env"))
    server_key = os.environ.get("SERVER_KEY")
    if not server_key:
        print("SERVER_KEY is missing from .env", file=sys.stderr)
        return 1

    try:
        response = requests.get(
            "https://api.erlc.gg/v2/server",
            headers={"Accept": "application/json", "server-key": server_key},
            timeout=20,
        )
    except requests.RequestException as error:
        print(f"API request failed: {error}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        print(f"API responding with HTTP {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1

    data = response.json()
    print("API responding: HTTP 200")
    print(f"Server: {data.get('Name', 'unknown')}")
    print(
        "Players: "
        f"{data.get('CurrentPlayers', 'unknown')}/"
        f"{data.get('MaxPlayers', 'unknown')}"
        

    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

def run_command(command: str) -> bool:
    server_key = os.environ.get("SERVER_KEY")

    if not server_key:
        raise RuntimeError("SERVER_KEY is missing.")

    try:
        response = requests.post(
            "https://api.erlc.gg/v1/server/command",
            headers={
                "server-key": server_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "command": command
            },
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(f"Failed to execute command: {e}")
        return False

    print("Command executed successfully!")
    return True
        

     

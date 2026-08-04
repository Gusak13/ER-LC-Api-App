import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
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


@dataclass(frozen=True)
class Settings:
    server_key: str
    command_allowlist: frozenset[str]
    app_name: str = "ER:LC Control Panel"


@lru_cache
def get_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")

    server_key = os.environ.get("SERVER_KEY", "").strip()
    if not server_key:
        raise RuntimeError("SERVER_KEY is missing from the environment or .env")

    raw_allowlist = os.environ.get("COMMAND_ALLOWLIST", "h,m")
    command_allowlist = frozenset(
        command.strip().lower().lstrip(":")
        for command in raw_allowlist.split(",")
        if command.strip()
    )
    return Settings(
        server_key=server_key,
        command_allowlist=command_allowlist,
    )

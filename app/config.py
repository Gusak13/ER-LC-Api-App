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
        name = name.strip()
        if name == "SERVER_KEY":
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


@dataclass(frozen=True)
class Settings:
    command_allowlist: frozenset[str]
    app_name: str = "ER:LC Control Panel"
    session_idle_seconds: int = 30 * 60
    session_absolute_seconds: int = 8 * 60 * 60
    session_cookie_secure: bool = False


def _positive_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _boolean(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


@lru_cache
def get_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")

    raw_allowlist = os.environ.get("COMMAND_ALLOWLIST", "*")
    command_allowlist = frozenset(
        command.strip().lower().lstrip(":")
        for command in raw_allowlist.split(",")
        if command.strip()
    )
    return Settings(
        command_allowlist=command_allowlist,
        session_idle_seconds=_positive_int("SESSION_IDLE_SECONDS", 30 * 60),
        session_absolute_seconds=_positive_int("SESSION_ABSOLUTE_SECONDS", 8 * 60 * 60),
        session_cookie_secure=_boolean("SESSION_COOKIE_SECURE", False),
    )

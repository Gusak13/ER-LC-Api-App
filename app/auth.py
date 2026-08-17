from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.client import ERLCClient

SESSION_COOKIE_NAME = "erlc_session"


@dataclass
class AuthSession:
    client: ERLCClient
    server_name: str
    created_at: float
    last_seen_at: float


class SessionStore:
    def __init__(
        self,
        *,
        idle_seconds: int,
        absolute_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._idle_seconds = idle_seconds
        self._absolute_seconds = absolute_seconds
        self._clock = clock
        self._sessions: dict[str, AuthSession] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create(self, client: ERLCClient, server_name: str) -> str:
        token = secrets.token_urlsafe(32)
        now = self._clock()
        session = AuthSession(
            client=client,
            server_name=server_name,
            created_at=now,
            last_seen_at=now,
        )
        with self._lock:
            self._purge_expired_locked(now)
            self._sessions[self._digest(token)] = session
        return token

    def get(self, token: str | None, *, touch: bool = True) -> AuthSession | None:
        if not token:
            return None
        now = self._clock()
        with self._lock:
            self._purge_expired_locked(now)
            session = self._sessions.get(self._digest(token))
            if session is not None and touch:
                session.last_seen_at = now
            return session

    def delete(self, token: str | None) -> None:
        if not token:
            return
        with self._lock:
            session = self._sessions.pop(self._digest(token), None)
        if session is not None:
            session.client.close()

    def close(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.client.close()

    def _purge_expired_locked(self, now: float) -> None:
        expired = [
            digest
            for digest, session in self._sessions.items()
            if now - session.last_seen_at >= self._idle_seconds
            or now - session.created_at >= self._absolute_seconds
        ]
        for digest in expired:
            self._sessions.pop(digest).client.close()


class LoginRateLimiter:
    def __init__(
        self,
        *,
        max_failures: int = 5,
        window_seconds: int = 15 * 60,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, client_id: str) -> int | None:
        now = self._clock()
        with self._lock:
            failures = self._failures.get(client_id)
            if failures is None:
                return None
            self._remove_old_failures(failures, now)
            if not failures:
                self._failures.pop(client_id, None)
                return None
            if len(failures) < self._max_failures:
                return None
            return max(1, int(self._window_seconds - (now - failures[0])))

    def record_failure(self, client_id: str) -> None:
        now = self._clock()
        with self._lock:
            failures = self._failures.setdefault(client_id, deque())
            self._remove_old_failures(failures, now)
            failures.append(now)

    def clear(self, client_id: str) -> None:
        with self._lock:
            self._failures.pop(client_id, None)

    def _remove_old_failures(self, failures: deque[float], now: float) -> None:
        cutoff = now - self._window_seconds
        while failures and failures[0] <= cutoff:
            failures.popleft()


def get_auth_session(request: Request, *, touch: bool = True) -> AuthSession | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return request.app.state.session_store.get(token, touch=touch)


def require_auth_session(request: Request) -> AuthSession:
    session = get_auth_session(request)
    if session is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return session


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if not origin or not host:
        raise HTTPException(status_code=403, detail="Same-origin request required")

    expected_origin = f"{request.url.scheme}://{host}"
    normalized_origin = origin.rstrip("/")
    if not secrets.compare_digest(normalized_origin, expected_origin):
        raise HTTPException(status_code=403, detail="Same-origin request required")

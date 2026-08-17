from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, SecretStr, field_validator

from app.auth import (
    SESSION_COOKIE_NAME,
    LoginRateLimiter,
    SessionStore,
    get_auth_session,
    require_same_origin,
)
from app.client import ERLCAPIError, ERLCClient
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    api_key: SecretStr = Field(min_length=8, max_length=512)

    @field_validator("api_key")
    @classmethod
    def clean_api_key(cls, api_key: SecretStr) -> SecretStr:
        value = api_key.get_secret_value().strip()
        if not value:
            raise ValueError("API key is required")
        return SecretStr(value)


class AuthStatus(BaseModel):
    authenticated: bool
    server_name: str | None = None


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=AuthStatus)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    _: Annotated[None, Depends(require_same_origin)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthStatus:
    limiter: LoginRateLimiter = request.app.state.login_rate_limiter
    client_id = _client_id(request)
    retry_after = limiter.retry_after(client_id)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Please wait before trying again.",
            headers={"Retry-After": str(retry_after)},
        )

    client_factory = request.app.state.client_factory
    client: ERLCClient = client_factory(payload.api_key.get_secret_value())
    try:
        server = client.get_server()
        server_name = server.get("Name")
        if not isinstance(server_name, str) or not server_name.strip():
            raise ERLCAPIError("ER:LC returned an unexpected server response")
    except ERLCAPIError as error:
        client.close()
        if error.status_code in {400, 401, 403}:
            limiter.record_failure(client_id)
            raise HTTPException(
                status_code=401,
                detail="That API key could not be verified.",
            ) from error
        raise HTTPException(
            status_code=502,
            detail="ER:LC is unavailable. Please try again later.",
        ) from error

    limiter.clear(client_id)
    store: SessionStore = request.app.state.session_store
    store.delete(request.cookies.get(SESSION_COOKIE_NAME))
    token = store.create(client, server_name.strip())
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.session_absolute_seconds,
        httponly=True,
        secure=settings.session_cookie_secure or request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return AuthStatus(authenticated=True, server_name=server_name.strip())


@router.get("/session", response_model=AuthStatus)
def session_status(request: Request) -> AuthStatus:
    session = get_auth_session(request)
    if session is None:
        return AuthStatus(authenticated=False)
    return AuthStatus(authenticated=True, server_name=session.server_name)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    _: Annotated[None, Depends(require_same_origin)],
) -> Response:
    request.app.state.session_store.delete(request.cookies.get(SESSION_COOKIE_NAME))
    response.status_code = 204
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=request.app.state.settings.session_cookie_secure
        or request.url.scheme == "https",
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return response

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import LoginRateLimiter, SessionStore, get_auth_session
from app.client import ERLCClient
from app.config import PROJECT_ROOT, get_settings
from app.routes.activity import router as activity_router
from app.routes.auth import router as auth_router
from app.routes.commands import router as commands_router
from app.routes.players import router as players_router
from app.routes.server import router as server_router

templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.client_factory = ERLCClient
    app.state.session_store = SessionStore(
        idle_seconds=settings.session_idle_seconds,
        absolute_seconds=settings.session_absolute_seconds,
    )
    app.state.login_rate_limiter = LoginRateLimiter()
    yield
    app.state.session_store.close()


app = FastAPI(title="ER:LC Control Panel", lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=PROJECT_ROOT / "app" / "static"),
    name="static",
)
app.mount(
    "/maps",
    StaticFiles(directory=PROJECT_ROOT / "Maps"),
    name="maps",
)
app.include_router(server_router)
app.include_router(commands_router)
app.include_router(players_router)
app.include_router(activity_router)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, error: RequestValidationError):
    if request.url.path == "/api/auth/login":
        return JSONResponse(
            status_code=400,
            content={"detail": "Enter a valid API key."},
            headers={"Cache-Control": "no-store"},
        )
    return await request_validation_exception_handler(request, error)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api/") or request.url.path in {
        "/",
        "/login",
        "/players",
        "/commands",
        "/activity",
        "/map",
        "/settings",
    }:
        response.headers["Cache-Control"] = "no-store"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


def _protected_page(request: Request, active_page: str):
    session = get_auth_session(request)
    if session is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": get_settings().app_name,
            "active_page": active_page,
            "server_name": session.server_name,
        },
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    if get_auth_session(request, touch=False) is not None:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"app_name": get_settings().app_name},
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return _protected_page(request, "dashboard")


@app.get("/players", response_class=HTMLResponse, include_in_schema=False)
def players_page(request: Request):
    return _protected_page(request, "players")


@app.get("/commands", response_class=HTMLResponse, include_in_schema=False)
def commands_page(request: Request):
    return _protected_page(request, "commands")


@app.get("/activity", response_class=HTMLResponse, include_in_schema=False)
def activity_page(request: Request):
    return _protected_page(request, "activity")


@app.get("/map", response_class=HTMLResponse, include_in_schema=False)
def map_page(request: Request):
    return _protected_page(request, "map")


@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
def settings_page(request: Request):
    return _protected_page(request, "settings")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}

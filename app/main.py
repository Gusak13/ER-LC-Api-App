from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.client import ERLCClient
from app.config import PROJECT_ROOT, get_settings
from app.routes.commands import router as commands_router
from app.routes.server import router as server_router
from app.services.command_service import CommandService

templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client = ERLCClient(settings.server_key)
    app.state.erlc_client = client
    app.state.command_service = CommandService(client, settings.command_allowlist)
    yield
    client.close()


app = FastAPI(title="ER:LC Control Panel", lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=PROJECT_ROOT / "app" / "static"),
    name="static",
)
app.include_router(server_router)
app.include_router(commands_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": get_settings().app_name},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}

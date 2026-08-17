from fastapi import Request

from app.auth import require_auth_session, require_same_origin
from app.client import ERLCClient
from app.services.command_service import CommandService


def get_erlc_client(request: Request) -> ERLCClient:
    return require_auth_session(request).client


def get_command_service(request: Request) -> CommandService:
    require_same_origin(request)
    settings = request.app.state.settings
    session = require_auth_session(request)
    return CommandService(session.client, settings.command_allowlist)

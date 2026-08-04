from fastapi import Request

from app.client import ERLCClient
from app.services.command_service import CommandService


def get_erlc_client(request: Request) -> ERLCClient:
    return request.app.state.erlc_client


def get_command_service(request: Request) -> CommandService:
    return request.app.state.command_service

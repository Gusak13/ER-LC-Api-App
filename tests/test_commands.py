import pytest
from pydantic import ValidationError

from app.schemas import CommandRequest
from app.services.command_service import CommandNotAllowedError, CommandService


class FakeClient:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def run_command(self, command: str) -> dict[str, str]:
        self.commands.append(command)
        return {"message": "Success"}


def test_command_schema_requires_colon_prefix() -> None:
    with pytest.raises(ValidationError):
        CommandRequest(command="h Hello")


def test_command_service_executes_allowlisted_command() -> None:
    client = FakeClient()
    service = CommandService(client, frozenset({"h"}))

    assert service.execute(":h Hello") == {"message": "Success"}
    assert client.commands == [":h Hello"]


def test_command_service_rejects_non_allowlisted_command() -> None:
    client = FakeClient()
    service = CommandService(client, frozenset({"h"}))

    with pytest.raises(CommandNotAllowedError):
        service.execute(":kick Player")

    assert client.commands == []

from app.client import ERLCClient


class CommandNotAllowedError(ValueError):
    pass


class CommandService:
    def __init__(self, client: ERLCClient, allowlist: frozenset[str]) -> None:
        self._client = client
        self._allowlist = allowlist

    def execute(self, command: str) -> dict:
        command_name = command[1:].split(maxsplit=1)[0].lower()
        if command_name not in self._allowlist:
            raise CommandNotAllowedError(
                f"Command ':{command_name}' is not enabled for this application"
            )
        return self._client.run_command(command)

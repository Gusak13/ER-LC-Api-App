from pydantic import BaseModel, Field, field_validator


class ServerSummary(BaseModel):
    name: str
    current_players: int
    max_players: int
    account_verification: str
    team_balance: bool

    @classmethod
    def from_api(cls, data: dict) -> ServerSummary:
        return cls(
            name=data["Name"],
            current_players=data["CurrentPlayers"],
            max_players=data["MaxPlayers"],
            account_verification=data["AccVerifiedReq"],
            team_balance=data["TeamBalance"],
        )


class CommandRequest(BaseModel):
    command: str = Field(min_length=2, max_length=200)

    @field_validator("command")
    @classmethod
    def validate_command(cls, command: str) -> str:
        command = command.strip()
        if not command.startswith(":"):
            raise ValueError("ER:LC commands must begin with ':'")
        return command


class CommandResult(BaseModel):
    message: str

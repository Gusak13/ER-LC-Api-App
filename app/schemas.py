from typing import Any

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


class PlayerSummary(BaseModel):
    username: str
    roblox_id: int | None
    team: str
    permission: str
    callsign: str | None
    wanted_stars: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PlayerSummary:
        raw_player = data.get("Player")
        player_value = raw_player if isinstance(raw_player, str) else "Unknown player"
        username, separator, raw_roblox_id = player_value.rpartition(":")

        roblox_id: int | None = None
        if separator and raw_roblox_id.isdigit():
            roblox_id = int(raw_roblox_id)
        else:
            username = player_value

        callsign = data.get("Callsign")
        wanted_stars = data.get("WantedStars")
        return cls(
            username=username or "Unknown player",
            roblox_id=roblox_id,
            team=str(data.get("Team") or "Unknown"),
            permission=str(data.get("Permission") or "Unknown"),
            callsign=callsign if isinstance(callsign, str) else None,
            wanted_stars=wanted_stars if isinstance(wanted_stars, int) else None,
        )


class PlayersResponse(BaseModel):
    players: list[PlayerSummary]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PlayersResponse:
        raw_players = data.get("Players", [])
        if not isinstance(raw_players, list):
            raise ValueError("ER:LC returned an invalid players list")
        return cls(players=[PlayerSummary.from_api(player) for player in raw_players])

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


class PlayerLocation(BaseModel):
    x: float | None
    z: float | None
    postal_code: str | None
    street_name: str | None
    building_number: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PlayerLocation:
        def optional_text(value: Any) -> str | None:
            return value.strip() if isinstance(value, str) and value.strip() else None

        raw_x = data.get("LocationX")
        raw_z = data.get("LocationZ")
        return cls(
            x=float(raw_x) if isinstance(raw_x, (int, float)) else None,
            z=float(raw_z) if isinstance(raw_z, (int, float)) else None,
            postal_code=optional_text(data.get("PostalCode")),
            street_name=optional_text(data.get("StreetName")),
            building_number=optional_text(data.get("BuildingNumber")),
        )


class PlayerSummary(BaseModel):
    username: str
    roblox_id: int | None
    team: str
    permission: str
    callsign: str | None
    wanted_stars: int | None
    location: PlayerLocation | None

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
        raw_location = data.get("Location")
        return cls(
            username=username or "Unknown player",
            roblox_id=roblox_id,
            team=str(data.get("Team") or "Unknown"),
            permission=str(data.get("Permission") or "Unknown"),
            callsign=callsign if isinstance(callsign, str) else None,
            wanted_stars=wanted_stars if isinstance(wanted_stars, int) else None,
            location=(
                PlayerLocation.from_api(raw_location)
                if isinstance(raw_location, dict)
                else None
            ),
        )


class PlayersResponse(BaseModel):
    players: list[PlayerSummary]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PlayersResponse:
        raw_players = data.get("Players", [])
        if not isinstance(raw_players, list):
            raise ValueError("ER:LC returned an invalid players list")
        return cls(players=[PlayerSummary.from_api(player) for player in raw_players])


class JoinLogEntry(BaseModel):
    player: str
    joined: bool
    timestamp: int


class KillLogEntry(BaseModel):
    killer: str
    killed: str
    timestamp: int


class CommandLogEntry(BaseModel):
    player: str
    command: str
    timestamp: int


class ModCallEntry(BaseModel):
    caller: str
    moderator: str | None
    timestamp: int


class BanEntry(BaseModel):
    player: str


class ActivityResponse(BaseModel):
    join_logs: list[JoinLogEntry]
    kill_logs: list[KillLogEntry]
    command_logs: list[CommandLogEntry]
    mod_calls: list[ModCallEntry]
    bans: list[BanEntry]

    @classmethod
    def from_api(
        cls,
        activity_data: dict[str, Any],
        bans_data: dict[str, Any] | list[Any],
    ) -> ActivityResponse:
        def records(key: str) -> list[dict[str, Any]]:
            raw_records = activity_data.get(key, [])
            if not isinstance(raw_records, list) or not all(
                isinstance(record, dict) for record in raw_records
            ):
                raise ValueError(f"ER:LC returned invalid {key}")
            return raw_records

        def text(record: dict[str, Any], key: str, fallback: str = "Unknown") -> str:
            value = record.get(key)
            return value if isinstance(value, str) and value else fallback

        def timestamp(record: dict[str, Any]) -> int:
            value = record.get("Timestamp")
            if not isinstance(value, int):
                raise ValueError("ER:LC returned an invalid timestamp")
            return value

        def ban_entry(value: Any, fallback: str) -> BanEntry:
            if isinstance(value, str) and value:
                return BanEntry(player=value)
            if isinstance(value, dict):
                for key in ("PlayerId", "Player", "Username"):
                    candidate = value.get(key)
                    if isinstance(candidate, str) and candidate:
                        return BanEntry(player=candidate)
            return BanEntry(player=fallback)

        if isinstance(bans_data, dict):
            ban_entries = [
                ban_entry(value, str(key)) for key, value in bans_data.items()
            ]
        elif isinstance(bans_data, list):
            ban_entries = [
                ban_entry(value, "Unknown banned player") for value in bans_data
            ]
        else:
            raise ValueError("ER:LC returned an invalid bans response")

        return cls(
            join_logs=[
                JoinLogEntry(
                    player=text(record, "Player"),
                    joined=bool(record.get("Join")),
                    timestamp=timestamp(record),
                )
                for record in records("JoinLogs")
            ],
            kill_logs=[
                KillLogEntry(
                    killer=text(record, "Killer"),
                    killed=text(record, "Killed"),
                    timestamp=timestamp(record),
                )
                for record in records("KillLogs")
            ],
            command_logs=[
                CommandLogEntry(
                    player=text(record, "Player"),
                    command=text(record, "Command"),
                    timestamp=timestamp(record),
                )
                for record in records("CommandLogs")
            ],
            mod_calls=[
                ModCallEntry(
                    caller=text(record, "Caller"),
                    moderator=(
                        record["Moderator"]
                        if isinstance(record.get("Moderator"), str)
                        else None
                    ),
                    timestamp=timestamp(record),
                )
                for record in records("ModCalls")
            ],
            bans=ban_entries,
        )

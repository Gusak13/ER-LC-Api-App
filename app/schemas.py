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


class DashboardStaffMember(BaseModel):
    username: str
    role: str
    team: str
    callsign: str | None


class DashboardWantedPlayer(BaseModel):
    username: str
    wanted_stars: int
    team: str


class EmergencyCallSummary(BaseModel):
    call_number: str
    caller: str
    team: str
    description: str
    position: str
    player_count: int


class VehicleSummary(BaseModel):
    name: str
    owner: str
    plate: str | None


class DashboardResponse(ServerSummary):
    team_counts: dict[str, int]
    staff_online: list[DashboardStaffMember]
    staff_counts: dict[str, int]
    wanted_players: list[DashboardWantedPlayer]
    queue: list[str]
    emergency_calls: list[EmergencyCallSummary]
    vehicles: list[VehicleSummary]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DashboardResponse:
        base = ServerSummary.from_api(data)

        def records(key: str) -> list[dict[str, Any]]:
            value = data.get(key, [])
            if not isinstance(value, list):
                raise ValueError(f"ER:LC returned an invalid {key}")
            return [record for record in value if isinstance(record, dict)]

        def text(value: Any, fallback: str) -> str:
            return (
                value.strip() if isinstance(value, str) and value.strip() else fallback
            )

        def player_name(value: Any) -> str:
            name = text(value, "Unknown player")
            username, separator, raw_id = name.rpartition(":")
            return username if separator and raw_id.isdigit() and username else name

        players = [PlayerSummary.from_api(player) for player in records("Players")]
        team_counts: dict[str, int] = {}
        for player in players:
            team_counts[player.team] = team_counts.get(player.team, 0) + 1

        civilian_permissions = {"", "civilian", "normal", "player", "unknown"}
        staff_online = [
            DashboardStaffMember(
                username=player.username,
                role=player.permission,
                team=player.team,
                callsign=player.callsign,
            )
            for player in players
            if player.permission.strip().lower() not in civilian_permissions
        ]

        raw_staff = data.get("Staff")
        staff_counts = {"Co-owners": 0, "Admins": 0, "Moderators": 0, "Helpers": 0}
        if isinstance(raw_staff, dict):
            co_owners = raw_staff.get("CoOwners", [])
            staff_counts["Co-owners"] = (
                len(co_owners) if isinstance(co_owners, list) else 0
            )
            for api_key, label in (
                ("Admins", "Admins"),
                ("Mods", "Moderators"),
                ("Helpers", "Helpers"),
            ):
                group = raw_staff.get(api_key, {})
                staff_counts[label] = len(group) if isinstance(group, dict) else 0

        wanted_players = [
            DashboardWantedPlayer(
                username=player.username,
                wanted_stars=player.wanted_stars or 0,
                team=player.team,
            )
            for player in players
            if (player.wanted_stars or 0) > 0
        ]
        wanted_players.sort(key=lambda player: player.wanted_stars, reverse=True)

        raw_queue = data.get("Queue", [])
        queue = (
            [str(player) for player in raw_queue] if isinstance(raw_queue, list) else []
        )

        emergency_calls = [
            EmergencyCallSummary(
                call_number=str(call.get("CallNumber") or "Active call"),
                caller=player_name(call.get("Caller")),
                team=text(call.get("Team"), "Unknown team"),
                description=text(call.get("Description"), "No description supplied"),
                position=text(call.get("PositionDescriptor"), "Location unavailable"),
                player_count=len(call.get("Players", []))
                if isinstance(call.get("Players"), list)
                else 0,
            )
            for call in records("EmergencyCalls")
        ]

        vehicles = [
            VehicleSummary(
                name=text(vehicle.get("Name"), "Unknown vehicle"),
                owner=player_name(vehicle.get("Owner")),
                plate=(
                    vehicle["Plate"].strip()
                    if isinstance(vehicle.get("Plate"), str)
                    and vehicle["Plate"].strip()
                    else None
                ),
            )
            for vehicle in records("Vehicles")
        ]

        return cls(
            **base.model_dump(),
            team_counts=team_counts,
            staff_online=staff_online,
            staff_counts=staff_counts,
            wanted_players=wanted_players,
            queue=queue,
            emergency_calls=emergency_calls,
            vehicles=vehicles,
        )


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

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.client import ERLCAPIError
from app.routes import get_command_service
from app.schemas import CommandRequest, CommandResult
from app.services.command_service import CommandNotAllowedError, CommandService

router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.post("", response_model=CommandResult)
def run_command(
    request: CommandRequest,
    service: Annotated[CommandService, Depends(get_command_service)],
) -> CommandResult:
    try:
        result = service.execute(request.command)
    except CommandNotAllowedError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ERLCAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return CommandResult(message=str(result.get("message", "Success")))

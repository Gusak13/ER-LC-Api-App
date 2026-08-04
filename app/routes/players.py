from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.client import ERLCAPIError, ERLCClient
from app.routes import get_erlc_client
from app.schemas import PlayersResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=PlayersResponse)
def get_players(
    client: Annotated[ERLCClient, Depends(get_erlc_client)],
) -> PlayersResponse:
    try:
        return PlayersResponse.from_api(client.get_players())
    except ERLCAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="ER:LC returned an unexpected players response",
        ) from error

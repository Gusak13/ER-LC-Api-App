from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.client import ERLCAPIError, ERLCClient
from app.routes import get_erlc_client
from app.schemas import ActivityResponse

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=ActivityResponse)
def get_activity(
    client: Annotated[ERLCClient, Depends(get_erlc_client)],
) -> ActivityResponse:
    try:
        return ActivityResponse.from_api(client.get_activity(), client.get_bans())
    except ERLCAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="ER:LC returned an unexpected activity response",
        ) from error

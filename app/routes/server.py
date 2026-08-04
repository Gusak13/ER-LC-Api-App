from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.client import ERLCAPIError, ERLCClient
from app.routes import get_erlc_client
from app.schemas import DashboardResponse, ServerSummary

router = APIRouter(prefix="/api/server", tags=["server"])


@router.get("", response_model=ServerSummary)
def get_server(
    client: Annotated[ERLCClient, Depends(get_erlc_client)],
) -> ServerSummary:
    try:
        return ServerSummary.from_api(client.get_server())
    except ERLCAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="ER:LC returned an unexpected server response",
        ) from error


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    client: Annotated[ERLCClient, Depends(get_erlc_client)],
) -> DashboardResponse:
    try:
        return DashboardResponse.from_api(client.get_dashboard())
    except ERLCAPIError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="ER:LC returned an unexpected dashboard response",
        ) from error

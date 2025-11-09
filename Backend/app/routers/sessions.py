from fastapi import APIRouter, Depends, HTTPException, Header, status

from ..auth import Principal, get_current_principal
from ..schemas import SessionStartResponse, SessionEndResponse
from ..session_manager import session_registry

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(principal: Principal = Depends(get_current_principal)):
    session_id, replaced = session_registry.start_session(principal.username)
    message = "Session started successfully."
    if replaced:
        message = "Existing session replaced with a new login."
    return SessionStartResponse(
        username=principal.username,
        session_id=session_id,
        replaced=replaced,
        message=message,
        access=principal.access.value,
    )


@router.post("/end", response_model=SessionEndResponse)
async def end_session(
    principal: Principal = Depends(get_current_principal),
    session_id: str | None = Header(default=None, alias="X-Session-Id"),
):
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    if not session_registry.validate(principal.username, session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active.",
        )
    ended = session_registry.end_session(principal.username)
    return SessionEndResponse(username=principal.username, ended=ended)

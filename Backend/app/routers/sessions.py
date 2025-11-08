from fastapi import APIRouter, Depends, HTTPException, Header, status

from ..auth import get_current_user
from ..schemas import SessionStartResponse, SessionEndResponse
from ..session_manager import session_registry

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(username: str = Depends(get_current_user)):
    session_id, replaced = session_registry.start_session(username)
    message = "Session started successfully."
    if replaced:
        message = "Existing session replaced with a new login."
    return SessionStartResponse(
        username=username,
        session_id=session_id,
        replaced=replaced,
        message=message,
    )


@router.post("/end", response_model=SessionEndResponse)
async def end_session(
    username: str = Depends(get_current_user),
    session_id: str | None = Header(default=None, alias="X-Session-Id"),
):
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    if not session_registry.validate(username, session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active.",
        )
    ended = session_registry.end_session(username)
    return SessionEndResponse(username=username, ended=ended)

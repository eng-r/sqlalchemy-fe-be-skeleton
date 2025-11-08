from typing import Generator

from fastapi import Depends, Header, HTTPException, status

from .auth import get_current_user
from .db import SessionLocal
from .session_manager import session_registry


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def require_active_session(
    username: str = Depends(get_current_user),
    session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> str:
    """Ensure the caller provides a valid session identifier for the user."""

    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    if not session_registry.validate(username, session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active. Please log in again.",
        )
    return username

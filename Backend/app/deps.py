from typing import Generator

from fastapi import Depends, Header, HTTPException, status

from .auth import Principal, get_current_principal
from .db import SessionLocal
from .session_manager import session_registry


def get_db(_: Principal = Depends(get_current_principal)) -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def require_active_session(
    principal: Principal = Depends(get_current_principal),
    session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> Principal:
    """Ensure the caller provides a valid session identifier for the user."""

    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id header is required",
        )
    if not session_registry.validate(principal.username, session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active. Please log in again.",
        )
    return principal

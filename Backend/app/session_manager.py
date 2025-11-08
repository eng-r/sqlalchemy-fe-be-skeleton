"""In-memory tracking of active user sessions."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional
from uuid import uuid4


@dataclass
class SessionInfo:
    """Simple container storing the server-side session identifier."""

    session_id: str


class SessionRegistry:
    """Store the most recent session identifier per username."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: Dict[str, SessionInfo] = {}

    def start_session(self, username: str) -> tuple[str, bool]:
        """Create a new session ID for ``username``.

        Returns a tuple ``(session_id, replaced)`` where ``replaced`` indicates
        whether a previous session for the same user was overwritten.
        """

        session_id = uuid4().hex
        with self._lock:
            replaced = username in self._sessions
            self._sessions[username] = SessionInfo(session_id=session_id)
        return session_id, replaced

    def end_session(self, username: str) -> bool:
        """Remove the session tracked for ``username``.

        Returns ``True`` if a session was present and has been removed.
        """

        with self._lock:
            return self._sessions.pop(username, None) is not None

    def validate(self, username: str, session_id: str) -> bool:
        """Check whether ``session_id`` matches the stored value for the user."""

        with self._lock:
            info = self._sessions.get(username)
            return bool(info and info.session_id == session_id)

    def get(self, username: str) -> Optional[SessionInfo]:
        with self._lock:
            return self._sessions.get(username)


session_registry = SessionRegistry()
"""Module-level singleton used by the API routers."""

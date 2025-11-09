import pytest
from fastapi import HTTPException

from app.auth.security import AccessLevel, Principal
from app.deps import require_active_session


@pytest.mark.asyncio
async def test_require_active_session_valid(monkeypatch):
    principal = Principal(username="analyst", access=AccessLevel.RD)
    monkeypatch.setattr("app.deps.session_registry.validate", lambda u, s: u == "analyst" and s == "valid")
    result = await require_active_session(principal, session_id="valid")
    assert result is principal


@pytest.mark.asyncio
async def test_require_active_session_missing_header():
    principal = Principal(username="user", access=AccessLevel.RD)
    with pytest.raises(HTTPException) as exc:
        await require_active_session(principal, session_id=None)
    assert exc.value.status_code == 400
    assert "X-Session-Id" in exc.value.detail


@pytest.mark.asyncio
async def test_require_active_session_invalid_session(monkeypatch):
    principal = Principal(username="user", access=AccessLevel.RD)
    monkeypatch.setattr("app.deps.session_registry.validate", lambda *_: False)
    with pytest.raises(HTTPException) as exc:
        await require_active_session(principal, session_id="wrong")
    assert exc.value.status_code == 401
    assert "Session is not active" in exc.value.detail

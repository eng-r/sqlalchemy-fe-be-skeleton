"""HTTP Basic authentication utilities with role-aware access control."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ..config import settings


security = HTTPBasic()


class SecretsLoadError(RuntimeError):
    """Raised when the credentials file cannot be read."""


class AccessLevel(str, Enum):
    """Supported access levels for authenticated users."""

    RD = "rd"
    WR = "wr"

    @property
    def can_write(self) -> bool:
        return self is AccessLevel.WR


@dataclass(frozen=True)
class Principal:
    """Authenticated user details used for access control."""

    username: str
    access: AccessLevel


_current_principal: ContextVar[Optional[Principal]] = ContextVar(
    "current_principal", default=None
)


UserSecret = Tuple[str, AccessLevel]


@lru_cache()
def _load_secrets(path: str) -> Dict[str, UserSecret]:
    """Load the hashed credentials from ``path``.

    The JSON file is expected to have the structure::

        {
            "algorithm": "bcrypt",
            "users": {
                "alice": {"hash": "<hash>", "access": "wr"},
                ...
            }
        }
    """

    secrets_path = Path(path)
    if not secrets_path.exists():
        raise SecretsLoadError(f"Secrets file not found: {secrets_path}")

    try:
        with secrets_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SecretsLoadError(f"Secrets file is not valid JSON: {secrets_path}") from exc

    users = payload.get("users")
    if not isinstance(users, dict):
        raise SecretsLoadError("Secrets file must contain a 'users' object")

    algorithm = payload.get("algorithm")
    if algorithm != "bcrypt":
        raise SecretsLoadError("Only bcrypt secrets are supported")

    cleaned: Dict[str, UserSecret] = {}
    for username, raw_entry in users.items():
        if not isinstance(username, str):
            raise SecretsLoadError("Invalid user entry in secrets file")

        hashed_password: Optional[str]
        access_value: Optional[str]
        if isinstance(raw_entry, str):
            hashed_password = raw_entry
            access_value = AccessLevel.WR.value
        elif isinstance(raw_entry, dict):
            hashed_password = raw_entry.get("hash")
            access_value = raw_entry.get("access")
        else:
            raise SecretsLoadError("Invalid user entry in secrets file")

        if not isinstance(hashed_password, str) or not hashed_password:
            raise SecretsLoadError(
                f"User '{username}' is missing a valid password hash"
            )
        if not isinstance(access_value, str) or not access_value:
            raise SecretsLoadError(
                f"User '{username}' is missing an access level"
            )

        try:
            access_level = AccessLevel(access_value.lower())
        except ValueError as exc:
            raise SecretsLoadError(
                f"User '{username}' has unsupported access level '{access_value}'"
            ) from exc

        cleaned[username] = (hashed_password, access_level)
    return cleaned


def _verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Raised when the hash is malformed
        return False


def _set_current_principal(principal: Principal) -> None:
    _current_principal.set(principal)


def get_active_principal() -> Optional[Principal]:
    """Return the principal stored for the current context, if any."""

    return _current_principal.get()


def _authenticate(credentials: HTTPBasicCredentials) -> Principal:
    try:
        secrets = _load_secrets(settings.SECRETS_FILE)
    except SecretsLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication backend unavailable",
        ) from exc

    secret = secrets.get(credentials.username)
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    hashed_password, access_level = secret
    if not _verify_password(hashed_password, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    principal = Principal(username=credentials.username, access=access_level)
    _set_current_principal(principal)
    return principal


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Validate HTTP Basic credentials and return the username."""

    principal = _authenticate(credentials)
    return principal.username


async def get_current_principal(
    credentials: HTTPBasicCredentials = Depends(security),
) -> Principal:
    """Validate credentials and return the authenticated principal."""

    return _authenticate(credentials)


def reload_secrets_cache() -> None:
    """Clear the cached secrets so that subsequent calls reload the file."""

    _load_secrets.cache_clear()

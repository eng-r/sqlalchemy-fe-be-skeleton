"""HTTP Basic authentication utilities."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ..config import settings


security = HTTPBasic()


class SecretsLoadError(RuntimeError):
    """Raised when the credentials file cannot be read."""


@lru_cache()
def _load_secrets(path: str) -> Dict[str, str]:
    """Load the hashed credentials from ``path``.

    The JSON file is expected to have the structure::

        {
            "algorithm": "bcrypt",
            "users": {"alice": "<hash>", ...}
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

    cleaned: Dict[str, str] = {}
    for username, hashed in users.items():
        if not isinstance(username, str) or not isinstance(hashed, str):
            raise SecretsLoadError("Invalid user entry in secrets file")
        cleaned[username] = hashed
    return cleaned


def _verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Raised when the hash is malformed
        return False


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Validate HTTP Basic credentials and return the username."""

    try:
        secrets = _load_secrets(settings.SECRETS_FILE)
    except SecretsLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication backend unavailable",
        ) from exc

    hashed_password = secrets.get(credentials.username)
    if not hashed_password or not _verify_password(
        hashed_password, credentials.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def reload_secrets_cache() -> None:
    """Clear the cached secrets so that subsequent calls reload the file."""

    _load_secrets.cache_clear()

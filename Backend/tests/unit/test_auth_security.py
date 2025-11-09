import json

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from app.auth.security import (
    AccessLevel,
    SecretsLoadError,
    get_current_user,
    reload_secrets_cache,
    _load_secrets,
)


@pytest.mark.asyncio
async def test_get_current_user_success(temp_secrets_file):
    temp_secrets_file({"alice": {"password": "wonderland", "access": "wr"}})
    credentials = HTTPBasicCredentials(username="alice", password="wonderland")
    username = await get_current_user(credentials)
    assert username == "alice"


@pytest.mark.asyncio
async def test_get_current_user_invalid_password(temp_secrets_file):
    temp_secrets_file({"alice": {"password": "wonderland", "access": "wr"}})
    credentials = HTTPBasicCredentials(username="alice", password="wrong")
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)
    assert exc.value.status_code == 401
    assert "Invalid username or password" in exc.value.detail


def test_load_secrets_from_valid_file(temp_secrets_file):
    path = temp_secrets_file({
        "writer": {"password": "secret123", "access": "wr"},
        "reader": {"password": "secret456", "access": "rd"},
    })
    secrets = _load_secrets(str(path))
    assert set(secrets.keys()) == {"writer", "reader"}
    assert secrets["reader"][1] == AccessLevel.RD


def test_load_secrets_missing_file_raises(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    with pytest.raises(SecretsLoadError):
        _load_secrets(str(missing_path))


def test_load_secrets_invalid_structure(tmp_path, monkeypatch):
    bad_file = tmp_path / "secrets.json"
    bad_file.write_text(json.dumps({"algorithm": "bcrypt", "users": []}), encoding="utf-8")
    with pytest.raises(SecretsLoadError):
        _load_secrets(str(bad_file))


def test_load_secrets_cache_is_cleared(temp_secrets_file):
    path = temp_secrets_file({"alice": {"password": "a", "access": "wr"}})
    first = _load_secrets(str(path))
    temp_secrets_file({"alice": {"password": "b", "access": "wr"}})
    reload_secrets_cache()
    second = _load_secrets(str(path))
    assert first["alice"] != second["alice"]

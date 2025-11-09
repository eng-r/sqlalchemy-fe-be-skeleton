# tests/conftest.py
import json
import os
import sys
from datetime import date
from pathlib import Path
from sqlalchemy.pool import StaticPool

"""
conftest.py is a special file recognized automatically by pytest - the shared configuration and fixture hub.
pytest auto-discovers it during test collection and uses it to share fixtures, hooks, and configuration across tests.

"""

# --- make local package imports reliable regardless of how pytest is invoked ---
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent  # points to Backend/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
os.environ.setdefault("PYTHONPATH", str(_PROJECT_ROOT))

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import deps
from app.auth.security import AccessLevel, Principal, reload_secrets_cache
from app.config import settings
from app.db import AccessControlledSession, Base
from app.models import Employee
from app.session_manager import SessionRegistry
from main import app


EMPLOYEE_FIXTURES = [
    {
        "emp_no": 10001,
        "birth_date": date(1953, 9, 2),
        "first_name": "Georgi",
        "last_name": "Facello",
        "gender": "M",
        "hire_date": date(1986, 6, 26),
    },
    {
        "emp_no": 10002,
        "birth_date": date(1964, 6, 2),
        "first_name": "Bezalel",
        "last_name": "Simmel",
        "gender": "F",
        "hire_date": date(1985, 11, 21),
    },
    {
        "emp_no": 10003,
        "birth_date": date(1959, 12, 3),
        "first_name": "Parto",
        "last_name": "Bamford",
        "gender": "M",
        "hire_date": date(1986, 8, 28),
    },
]

@pytest.fixture
def sqlite_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def session_factory(sqlite_engine):
    seed_session = sessionmaker(bind=sqlite_engine, future=True, expire_on_commit=False)
    with seed_session() as session:
        session.query(Employee).delete()
        for row in EMPLOYEE_FIXTURES:
            session.add(Employee(**row))
        session.commit()
    SessionLocal = sessionmaker(
        bind=sqlite_engine,
        class_=AccessControlledSession,
        autoflush=False,
        autocommit=False,
        future=True,
        expire_on_commit=False,
    )
    return SessionLocal


@pytest.fixture(autouse=True)
def isolate_session_registry(monkeypatch):
    registry = SessionRegistry()
    monkeypatch.setattr("app.session_manager.session_registry", registry)
    monkeypatch.setattr("app.deps.session_registry", registry)
    monkeypatch.setattr("app.routers.sessions.session_registry", registry)
    yield registry


@pytest.fixture
def set_active_principal(monkeypatch):
    def _setter(access_level: AccessLevel | None):
        if access_level is None:
            principal = None
        else:
            principal = Principal(username=f"{access_level.value}_user", access=access_level)
        monkeypatch.setattr("app.db.get_active_principal", lambda: principal)
        return principal

    return _setter


@pytest.fixture
def temp_secrets_file(tmp_path, monkeypatch):
    original_path = settings.SECRETS_FILE

    def _writer(users: dict[str, dict[str, str]]):
        secrets_path = tmp_path / "secrets.json"
        payload = {"algorithm": "bcrypt", "users": {}}
        for username, entry in users.items():
            password = entry["password"]
            access = entry["access"]
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            payload["users"][username] = {
                "hash": hashed.decode("utf-8"),
                "access": access,
            }
        secrets_path.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(settings, "SECRETS_FILE", str(secrets_path))
        reload_secrets_cache()
        return secrets_path

    yield _writer

    monkeypatch.setattr(settings, "SECRETS_FILE", original_path)
    reload_secrets_cache()


@pytest.fixture
def api_client(session_factory, temp_secrets_file, isolate_session_registry):
    users = {
        "admin": {"password": "supersecret", "access": "wr"},
        "analyst": {"password": "demo123", "access": "rd"},
    }
    temp_secrets_file(users)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[deps.get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def golden_employee() -> dict:
    path = Path(__file__).resolve().parent / "data" / "golden_employee.json"
    return json.loads(path.read_text(encoding="utf-8"))

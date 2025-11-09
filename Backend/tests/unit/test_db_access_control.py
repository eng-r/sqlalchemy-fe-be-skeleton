from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.auth.security import AccessLevel
from app.models import Employee


@pytest.fixture
def memory_engine(sqlite_engine):
    return sqlite_engine


def _create_employee(emp_no: int) -> Employee:
    return Employee(
        emp_no=emp_no,
        birth_date=date(1970, 1, 1),
        first_name="Test",
        last_name="Employee",
        gender="M",
        hire_date=date(2020, 1, 1),
    )


def test_read_only_principal_cannot_modify(session_factory, set_active_principal):
    set_active_principal(AccessLevel.RD)
    session = session_factory()
    try:
        with pytest.raises(HTTPException) as exc:
            session.add(_create_employee(20001))
        assert exc.value.status_code == 403
    finally:
        session.close()


def test_write_principal_can_commit(session_factory, set_active_principal):
    set_active_principal(AccessLevel.WR)
    session = session_factory()
    try:
        employee = _create_employee(20002)
        session.add(employee)
        session.commit()
        refreshed = session.get(Employee, 20002)
        assert refreshed is not None
        assert refreshed.first_name == "Test"
    finally:
        session.close()


def test_execute_blocks_write_statements_for_read_only(session_factory, set_active_principal):
    set_active_principal(AccessLevel.RD)
    session = session_factory()
    try:
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        with pytest.raises(HTTPException):
            session.execute(text("UPDATE employees SET last_name='X' WHERE emp_no=10001"))
    finally:
        session.close()


def test_execute_allows_writes_when_principal_is_none(session_factory, set_active_principal):
    set_active_principal(None)
    session = session_factory()
    try:
        employee = _create_employee(20003)
        session.add(employee)
        session.commit()
        assert session.get(Employee, 20003) is not None
    finally:
        session.close()

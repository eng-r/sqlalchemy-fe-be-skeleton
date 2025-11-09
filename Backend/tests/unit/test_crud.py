from app import crud
from app.auth.security import AccessLevel
from app.models import Employee


def test_get_employees_returns_rows(session_factory, set_active_principal):
    set_active_principal(AccessLevel.RD)
    session = session_factory()
    try:
        rows = crud.get_employees(session, limit=2, offset=0)
        assert len(rows) == 2
        emp_numbers = [row.emp_no for row in rows]
        assert emp_numbers == [10001, 10002]
    finally:
        session.close()


def test_get_employee_returns_model(session_factory, set_active_principal):
    set_active_principal(AccessLevel.RD)
    session = session_factory()
    try:
        employee = crud.get_employee(session, 10001)
        assert isinstance(employee, Employee)
        assert employee.first_name == "Georgi"
    finally:
        session.close()


def test_get_employee_returns_none_for_unknown(session_factory, set_active_principal):
    set_active_principal(AccessLevel.RD)
    session = session_factory()
    try:
        assert crud.get_employee(session, 99999) is None
    finally:
        session.close()


def test_update_employee_last_name(session_factory, set_active_principal):
    set_active_principal(AccessLevel.WR)
    session = session_factory()
    try:
        updated = crud.update_employee_last_name(session, 10001, "Updated")
        assert updated is not None
        assert updated.last_name == "Updated"
        refreshed = session.get(Employee, 10001)
        assert refreshed.last_name == "Updated"
    finally:
        session.close()


def test_update_employee_last_name_missing_employee(session_factory, set_active_principal):
    set_active_principal(AccessLevel.WR)
    session = session_factory()
    try:
        assert crud.update_employee_last_name(session, 99999, "Updated") is None
    finally:
        session.close()

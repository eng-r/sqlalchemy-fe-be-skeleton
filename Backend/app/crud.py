from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Employee


def get_employees(session: Session, *, limit: int = 10, offset: int = 0):
    stmt = (
        select(Employee.emp_no, Employee.first_name, Employee.last_name)
        .order_by(Employee.emp_no)
        .offset(offset)
        .limit(limit)
    )
    return session.execute(stmt).all()


def get_employee(session: Session, emp_no: int) -> Employee | None:
    return session.get(Employee, emp_no)


def update_employee_last_name(session: Session, emp_no: int, last_name: str) -> Employee | None:
    employee = session.get(Employee, emp_no)
    if employee is None:
        return None
    employee.last_name = last_name
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee

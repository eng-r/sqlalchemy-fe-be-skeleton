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

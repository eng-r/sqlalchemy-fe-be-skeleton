from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import Principal, get_current_user
from ..deps import get_db, require_active_session
from .. import crud
from ..schemas import (
    EmployeeLastNameUpdate,
    EmployeeOut,
)


router = APIRouter()


@router.get("", response_model=list[EmployeeOut])  # /employees
@router.get("/", response_model=list[EmployeeOut])  # /employees/
async def list_employees(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    rows = crud.get_employees(db, limit=limit, offset=offset)
    return [
        {"emp_no": r.emp_no, "first_name": r.first_name, "last_name": r.last_name}
        for r in rows
    ]


@router.get("/{emp_no}", response_model=EmployeeOut)
async def get_employee(
    emp_no: int,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(require_active_session),
):
    employee = crud.get_employee(db, emp_no)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_no} not found",
        )
    return EmployeeOut.model_validate(employee)


@router.put("/{emp_no}/last-name", response_model=EmployeeOut)
async def update_employee_last_name(
    emp_no: int,
    payload: EmployeeLastNameUpdate,
    db: Session = Depends(get_db),
    _principal: Principal = Depends(require_active_session),
):
    employee = crud.update_employee_last_name(db, emp_no, payload.last_name)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {emp_no} not found",
        )
    return EmployeeOut.model_validate(employee)

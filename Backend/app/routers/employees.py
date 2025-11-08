from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..deps import get_db
from .. import crud
from ..schemas import EmployeeOut


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

from pydantic import BaseModel


class EmployeeOut(BaseModel):
    emp_no: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

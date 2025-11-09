from pydantic import BaseModel, Field


class EmployeeOut(BaseModel):
    emp_no: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class EmployeeLastNameUpdate(BaseModel):
    last_name: str = Field(..., min_length=1, max_length=16)


class SessionStartResponse(BaseModel):
    username: str
    session_id: str
    replaced: bool
    message: str
    access: str


class SessionEndResponse(BaseModel):
    username: str
    ended: bool

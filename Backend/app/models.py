from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date
from .db import Base


class Employee(Base):
    __tablename__ = "employees"

    emp_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    birth_date: Mapped[Date] = mapped_column(Date, nullable=False)
    first_name: Mapped[str] = mapped_column(String(14), nullable=False)
    last_name: Mapped[str] = mapped_column(String(16), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    hire_date: Mapped[Date] = mapped_column(Date, nullable=False)

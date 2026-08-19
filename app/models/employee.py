import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class EmployeeRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(EmployeeRole), nullable=False, default=EmployeeRole.employee)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    vacation_allocations = relationship(
        "VacationAllocation", back_populates="employee", cascade="all, delete-orphan"
    )
    used_vacation_records = relationship(
        "UsedVacationRecord", back_populates="employee", cascade="all, delete-orphan"
    )

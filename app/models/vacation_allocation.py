from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class VacationAllocation(Base):
    __tablename__ = "vacation_allocations"
    __table_args__ = (
        UniqueConstraint("employee_id", "year", name="uq_vacation_allocation_employee_year"),
    )

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False)

    employee = relationship("Employee", back_populates="vacation_allocations")

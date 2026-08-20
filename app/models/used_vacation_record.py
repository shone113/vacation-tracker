from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.database import Base


class UsedVacationRecord(Base):
    __tablename__ = "used_vacation_records"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_used_vacation_record_end_after_start"),
    )

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    employee = relationship("Employee", back_populates="used_vacation_records")

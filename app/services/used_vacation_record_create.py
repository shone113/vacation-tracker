from datetime import date

from sqlalchemy.orm import Session

from app.models.used_vacation_record import UsedVacationRecord
from app.services.date_ranges import periods_overlap, weekdays_in_year
from app.services.vacation_summary import get_vacation_summary


class OverlapError(Exception):
    def __init__(self, conflicting_start: date, conflicting_end: date):
        self.conflicting_start = conflicting_start
        self.conflicting_end = conflicting_end
        super().__init__(
            f"Overlaps existing period {conflicting_start.isoformat()} to {conflicting_end.isoformat()}"
        )


class NoWorkingDaysError(Exception):
    def __init__(self):
        super().__init__("Period contains no working days (weekends only)")


class InsufficientAllowanceError(Exception):
    def __init__(self, year: int, requested_days: int, available_days: int):
        self.year = year
        self.requested_days = requested_days
        self.available_days = available_days
        super().__init__(
            f"Requested {requested_days} working day(s) in {year} but only {available_days} available"
        )


def create_used_vacation_record(
    db: Session, employee_id: int, start_date: date, end_date: date
) -> UsedVacationRecord:
    existing = (
        db.query(UsedVacationRecord).filter(UsedVacationRecord.employee_id == employee_id).all()
    )
    for record in existing:
        if periods_overlap(start_date, end_date, record.start_date, record.end_date):
            raise OverlapError(record.start_date, record.end_date)

    days_per_year = {
        year: weekdays_in_year(start_date, end_date, year)
        for year in range(start_date.year, end_date.year + 1)
    }
    days_per_year = {year: days for year, days in days_per_year.items() if days > 0}

    if not days_per_year:
        raise NoWorkingDaysError()

    for year, requested_days in days_per_year.items():
        summary = get_vacation_summary(db, employee_id=employee_id, year=year)
        if requested_days > summary.available_days:
            raise InsufficientAllowanceError(year, requested_days, summary.available_days)

    record = UsedVacationRecord(employee_id=employee_id, start_date=start_date, end_date=end_date)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

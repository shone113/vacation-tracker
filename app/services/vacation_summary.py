from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.used_vacation_record import UsedVacationRecord
from app.models.vacation_allocation import VacationAllocation


@dataclass
class VacationSummary:
    year: int
    total_days: int
    used_days: int
    available_days: int


def _weekdays_in_range(start: date, end: date) -> int:
    days = (end - start).days + 1
    return sum(1 for i in range(days) if (start + timedelta(days=i)).weekday() < 5)


def _weekdays_used_in_year(start_date: date, end_date: date, year: int) -> int:
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    intersection_start = max(start_date, year_start)
    intersection_end = min(end_date, year_end)
    if intersection_start > intersection_end:
        return 0

    return _weekdays_in_range(intersection_start, intersection_end)


def get_years_with_data(db: Session, employee_id: int) -> list[int]:
    allocation_years = {
        year
        for (year,) in db.query(VacationAllocation.year)
        .filter(VacationAllocation.employee_id == employee_id)
        .distinct()
        .all()
    }

    record_years: set[int] = set()
    for start_date, end_date in (
        db.query(UsedVacationRecord.start_date, UsedVacationRecord.end_date)
        .filter(UsedVacationRecord.employee_id == employee_id)
        .all()
    ):
        record_years.update(range(start_date.year, end_date.year + 1))

    return sorted(allocation_years | record_years)


def get_vacation_summary(db: Session, employee_id: int, year: int) -> VacationSummary:
    allocation = (
        db.query(VacationAllocation)
        .filter(VacationAllocation.employee_id == employee_id, VacationAllocation.year == year)
        .first()
    )
    total_days = allocation.total_days if allocation else 0

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    records = (
        db.query(UsedVacationRecord)
        .filter(
            UsedVacationRecord.employee_id == employee_id,
            UsedVacationRecord.start_date <= year_end,
            UsedVacationRecord.end_date >= year_start,
        )
        .all()
    )

    used_days = sum(_weekdays_used_in_year(r.start_date, r.end_date, year) for r in records)

    return VacationSummary(
        year=year,
        total_days=total_days,
        used_days=used_days,
        available_days=total_days - used_days,
    )

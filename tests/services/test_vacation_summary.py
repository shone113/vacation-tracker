from datetime import date

from app.models.used_vacation_record import UsedVacationRecord
from app.models.vacation_allocation import VacationAllocation
from app.services.vacation_summary import get_vacation_summary


def test_no_data_returns_zeros(db, employee):
    summary = get_vacation_summary(db, employee_id=employee.id, year=2020)
    assert summary.total_days == 0
    assert summary.used_days == 0
    assert summary.available_days == 0


def test_used_days_excludes_weekends(db, employee):
    db.add(VacationAllocation(employee_id=employee.id, year=2020, total_days=20))
    db.add(UsedVacationRecord(employee_id=employee.id, start_date=date(2020, 8, 3), end_date=date(2020, 8, 9)))
    db.flush()

    summary = get_vacation_summary(db, employee_id=employee.id, year=2020)
    assert summary.used_days == 5  # Mon-Fri only
    assert summary.available_days == 15


def test_cross_year_period_splits_between_years(db, employee):
    db.add(VacationAllocation(employee_id=employee.id, year=2020, total_days=20))
    db.add(VacationAllocation(employee_id=employee.id, year=2021, total_days=20))
    db.add(UsedVacationRecord(employee_id=employee.id, start_date=date(2020, 12, 28), end_date=date(2021, 1, 6)))
    db.flush()

    assert get_vacation_summary(db, employee_id=employee.id, year=2020).used_days == 4
    assert get_vacation_summary(db, employee_id=employee.id, year=2021).used_days == 4

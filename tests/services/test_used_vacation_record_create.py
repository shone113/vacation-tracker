from datetime import date

import pytest

from app.models.vacation_allocation import VacationAllocation
from app.services.used_vacation_record_create import (
    InsufficientAllowanceError,
    NoWorkingDaysError,
    OverlapError,
    create_used_vacation_record,
)


def _allocate(db, employee_id, year, total_days):
    db.add(VacationAllocation(employee_id=employee_id, year=year, total_days=total_days))
    db.flush()


def test_creates_record_within_allowance(db, employee):
    _allocate(db, employee.id, 2020, 20)
    record = create_used_vacation_record(db, employee.id, date(2020, 8, 3), date(2020, 8, 5))
    assert record.id is not None


def test_rejects_overlap_with_existing_record(db, employee):
    _allocate(db, employee.id, 2020, 20)
    create_used_vacation_record(db, employee.id, date(2020, 8, 3), date(2020, 8, 7))

    with pytest.raises(OverlapError):
        create_used_vacation_record(db, employee.id, date(2020, 8, 5), date(2020, 8, 10))


def test_rejects_weekend_only_period(db, employee):
    _allocate(db, employee.id, 2020, 20)
    with pytest.raises(NoWorkingDaysError):
        create_used_vacation_record(db, employee.id, date(2020, 8, 8), date(2020, 8, 9))  # Sat-Sun


def test_rejects_when_exceeding_allowance(db, employee):
    _allocate(db, employee.id, 2020, 2)
    with pytest.raises(InsufficientAllowanceError):
        create_used_vacation_record(db, employee.id, date(2020, 8, 3), date(2020, 8, 7))  # 5 weekdays


def test_cross_year_period_rejected_if_one_year_has_no_room(db, employee):
    _allocate(db, employee.id, 2020, 20)
    _allocate(db, employee.id, 2021, 0)

    with pytest.raises(InsufficientAllowanceError):
        create_used_vacation_record(db, employee.id, date(2020, 12, 28), date(2021, 1, 1))

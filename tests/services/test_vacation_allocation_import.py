from app.models.vacation_allocation import VacationAllocation
from app.services.vacation_allocation_import import import_vacation_allocations_from_file


def _csv(year, *rows):
    return (f"Vacation year,{year}\nEmployee,Total vacation days\n" + "\n".join(rows)).encode()


def test_creates_new_allocation(db, make_employee):
    make_employee("user1@test.local", "x")
    result = import_vacation_allocations_from_file(_csv(2021, "user1@test.local,20"), "v.csv", db)
    assert result.created == 1
    assert result.updated == 0


def test_updates_existing_allocation(db, make_employee):
    emp = make_employee("user1@test.local", "x")
    db.add(VacationAllocation(employee_id=emp.id, year=2021, total_days=15))
    db.flush()

    result = import_vacation_allocations_from_file(_csv(2021, "user1@test.local,20"), "v.csv", db)
    assert result.updated == 1
    allocation = db.query(VacationAllocation).filter_by(employee_id=emp.id).first()
    assert allocation.total_days == 20


def test_unknown_employee_fails_row(db):
    result = import_vacation_allocations_from_file(_csv(2021, "ghost@test.local,20"), "v.csv", db)
    assert result.created == 0
    assert result.failed == 1
    assert result.errors[0].reason == "Employee not found"


def test_duplicate_employee_in_file_fails_both_rows(db, make_employee):
    make_employee("user1@test.local", "x")
    content = _csv(2021, "user1@test.local,20", "user1@test.local,25")
    result = import_vacation_allocations_from_file(content, "v.csv", db)
    assert result.created == 0
    assert result.failed == 2

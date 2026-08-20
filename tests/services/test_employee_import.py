import pytest

from app.models.employee import Employee, EmployeeRole
from app.services.employee_import import import_employees_from_csv


def _csv(*rows):
    return ("Vacation year,2019\nEmployee Email,Employee Password\n" + "\n".join(rows)).encode()


def test_imports_new_employees_as_employee_role(db):
    result = import_employees_from_csv(_csv("user1@test.local,Abc123!"), db)
    assert result.imported == 1

    emp = db.query(Employee).filter(Employee.email == "user1@test.local").first()
    assert emp.role == EmployeeRole.employee
    assert emp.hashed_password != "Abc123!"


def test_skips_existing_email(db, make_employee):
    make_employee("user1@test.local", "whatever")
    result = import_employees_from_csv(_csv("user1@test.local,Abc123!", "user2@test.local,Abc123!"), db)
    assert result.imported == 1
    assert result.skipped_existing == 1


def test_missing_header_raises_error(db):
    with pytest.raises(ValueError):
        import_employees_from_csv(b"not,a,valid,header\nfoo,bar", db)

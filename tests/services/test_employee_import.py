import io

import pandas as pd
import pytest

from app.models.employee import Employee, EmployeeRole
from app.services.employee_import import import_employees_from_file


def _csv(*rows):
    return ("Vacation year,2019\nEmployee Email,Employee Password\n" + "\n".join(rows)).encode()


def _xlsx(rows):
    buf = io.BytesIO()
    df = pd.DataFrame(rows, columns=["Employee Email", "Employee Password"])
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def test_imports_new_employees_as_employee_role(db):
    result = import_employees_from_file(_csv("user1@test.local,Abc123!"), "employees.csv", db)
    assert result.imported == 1

    emp = db.query(Employee).filter(Employee.email == "user1@test.local").first()
    assert emp.role == EmployeeRole.employee
    assert emp.hashed_password != "Abc123!"


def test_skips_existing_email(db, make_employee):
    make_employee("user1@test.local", "whatever")
    content = _csv("user1@test.local,Abc123!", "user2@test.local,Abc123!")
    result = import_employees_from_file(content, "employees.csv", db)
    assert result.imported == 1
    assert result.skipped_existing == 1


def test_missing_header_raises_error(db):
    with pytest.raises(ValueError):
        import_employees_from_file(b"not,a,valid,header\nfoo,bar", "employees.csv", db)


def test_imports_from_excel_file(db):
    content = _xlsx([["user1@test.local", "Abc123!"]])
    result = import_employees_from_file(content, "employees.xlsx", db)
    assert result.imported == 1
    assert db.query(Employee).filter(Employee.email == "user1@test.local").first() is not None

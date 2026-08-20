from datetime import date

from app.models.used_vacation_record import UsedVacationRecord
from tests.conftest import auth_headers


def test_employees_response_has_no_password_field(client, admin):
    response = client.get("/admin/employees", headers=auth_headers(admin.email, "Test1234!"))
    for item in response.json()["items"]:
        assert "hashed_password" not in item


def test_used_vacation_records_overlap_filter(client, admin, employee, db):
    db.add(UsedVacationRecord(employee_id=employee.id, start_date=date(2020, 12, 28), end_date=date(2021, 1, 6)))
    db.flush()

    response = client.get(
        "/admin/used-vacation-records?from_date=2021-01-01&to_date=2021-01-31",
        headers=auth_headers(admin.email, "Test1234!"),
    )
    assert response.json()["total"] == 1

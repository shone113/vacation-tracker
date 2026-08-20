from datetime import date

from app.models.used_vacation_record import UsedVacationRecord
from app.models.vacation_allocation import VacationAllocation
from tests.conftest import auth_headers


def _auth(employee):
    return auth_headers(employee.email, "Test1234!")


def test_vacation_summary_without_year_returns_all_years(client, employee, db):
    db.add(VacationAllocation(employee_id=employee.id, year=2019, total_days=20))
    db.add(VacationAllocation(employee_id=employee.id, year=2020, total_days=20))
    db.flush()

    response = client.get("/me/vacation-summary", headers=_auth(employee))
    years = [item["year"] for item in response.json()]
    assert years == [2019, 2020]


def test_used_vacation_records_only_returns_own_records(client, employee, make_employee, db):
    other = make_employee("other@test.local", "Test1234!")
    db.add(UsedVacationRecord(employee_id=employee.id, start_date=date(2020, 8, 3), end_date=date(2020, 8, 3)))
    db.add(UsedVacationRecord(employee_id=other.id, start_date=date(2020, 9, 1), end_date=date(2020, 9, 1)))
    db.flush()

    response = client.get("/me/used-vacation-records", headers=_auth(employee))
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["employee_id"] == employee.id


def test_add_record_success_returns_201(client, employee, db):
    db.add(VacationAllocation(employee_id=employee.id, year=2020, total_days=20))
    db.flush()

    response = client.post(
        "/me/used-vacation-records",
        headers=_auth(employee),
        json={"start_date": "2020-08-03", "end_date": "2020-08-05"},
    )
    assert response.status_code == 201


def test_add_record_overlap_returns_409(client, employee, db):
    db.add(VacationAllocation(employee_id=employee.id, year=2020, total_days=20))
    db.add(UsedVacationRecord(employee_id=employee.id, start_date=date(2020, 8, 3), end_date=date(2020, 8, 7)))
    db.flush()

    response = client.post(
        "/me/used-vacation-records",
        headers=_auth(employee),
        json={"start_date": "2020-08-05", "end_date": "2020-08-10"},
    )
    assert response.status_code == 409

from tests.conftest import auth_headers


def _upload(client, admin, path, content):
    return client.post(
        path, headers=auth_headers(admin.email, "Test1234!"), files={"file": ("data.csv", content, "text/csv")}
    )


def test_employees_import_success(client, admin):
    content = b"Employee Email,Employee Password\nuser1@test.local,Abc123!\n"
    response = _upload(client, admin, "/admin/employees/import", content)
    assert response.status_code == 200
    assert response.json()["imported"] == 1


def test_used_vacation_records_import_success(client, admin, make_employee):
    make_employee("user1@test.local", "x")
    content = (
        b"Employee,Vacation start date,Vacation end date\n"
        b'user1@test.local,"Monday, August 3, 2020","Friday, August 7, 2020"\n'
    )
    response = _upload(client, admin, "/admin/used-vacation-records/import", content)
    assert response.status_code == 200
    assert response.json()["created"] == 1

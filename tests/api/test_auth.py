from tests.conftest import auth_headers


def test_no_credentials_returns_401(client):
    response = client.get("/me")
    assert response.status_code == 401


def test_valid_credentials_return_200(client, employee):
    response = client.get("/me", headers=auth_headers(employee.email, "Test1234!"))
    assert response.status_code == 200
    assert response.json()["email"] == employee.email


def test_employee_forbidden_from_admin_route(client, employee):
    response = client.get("/admin/employees", headers=auth_headers(employee.email, "Test1234!"))
    assert response.status_code == 403

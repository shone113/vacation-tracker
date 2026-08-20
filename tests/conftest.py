import base64
from urllib.parse import urlparse, urlunparse

import psycopg2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  needed so all tables are registered
from app.core.config import settings
from app.core.security import hash_password
from app.db.database import Base, get_db
from app.main import app
from app.models.employee import Employee, EmployeeRole

# use a separate database so tests never touch real data
parsed = urlparse(settings.database_url)
TEST_DB_NAME = parsed.path.lstrip("/") + "-test"
TEST_DATABASE_URL = urlunparse(parsed._replace(path=f"/{TEST_DB_NAME}"))


def _create_test_database_if_missing():
    conn = psycopg2.connect(
        dbname="postgres", user=parsed.username, password=parsed.password, host=parsed.hostname, port=parsed.port
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    cur.close()
    conn.close()


_create_test_database_if_missing()
engine = create_engine(TEST_DATABASE_URL)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    yield session
    session.close()
    with engine.connect() as conn:
        conn.execute(Employee.__table__.delete())
        conn.commit()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_employee(db):
    def _make(email, password, role=EmployeeRole.employee):
        emp = Employee(email=email, hashed_password=hash_password(password), role=role)
        db.add(emp)
        db.flush()
        return emp

    return _make


@pytest.fixture
def employee(make_employee):
    return make_employee("employee@test.local", "Test1234!")


@pytest.fixture
def admin(make_employee):
    return make_employee("admin@test.local", "Test1234!", EmployeeRole.admin)


def auth_headers(email, password):
    token = base64.b64encode(f"{email}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

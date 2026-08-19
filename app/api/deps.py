from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.database import get_db
from app.models.employee import Employee, EmployeeRole

security = HTTPBasic()


def get_current_employee(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Employee:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Basic"},
    )

    employee = db.query(Employee).filter(Employee.email == credentials.username).first()
    if employee is None or not verify_password(credentials.password, employee.hashed_password):
        raise unauthorized

    return employee


def get_current_admin(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role != EmployeeRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return employee

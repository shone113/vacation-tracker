from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_employee
from app.db.database import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeOut
from app.schemas.vacation_summary import VacationSummaryOut
from app.services.vacation_summary import get_vacation_summary, get_years_with_data

router = APIRouter(prefix="/me", tags=["employee"])


@router.get("", response_model=EmployeeOut)
def read_current_employee(current_employee: Employee = Depends(get_current_employee)):
    return current_employee


@router.get("/vacation-summary", response_model=list[VacationSummaryOut])
def get_my_vacation_summary(
    year: int | None = Query(
        None, description="Calendar year. If omitted, returns a breakdown for every year with data."
    ),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    years = [year] if year is not None else get_years_with_data(db, employee_id=current_employee.id)
    return [get_vacation_summary(db, employee_id=current_employee.id, year=y) for y in years]

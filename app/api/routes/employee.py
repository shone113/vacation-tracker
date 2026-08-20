from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_employee
from app.db.database import get_db
from app.models.employee import Employee
from app.schemas.common import Page
from app.schemas.employee import EmployeeOut
from app.schemas.used_vacation_record import UsedVacationRecordOut
from app.schemas.vacation_summary import VacationSummaryOut
from app.services.used_vacation_record_query import list_used_vacation_records
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


@router.get("/used-vacation-records", response_model=Page[UsedVacationRecordOut])
def get_my_used_vacation_records(
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="from_date must be before or equal to to_date"
        )

    items, total = list_used_vacation_records(
        db,
        employee_id=current_employee.id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return Page(items=items, total=total, page=page, page_size=page_size)

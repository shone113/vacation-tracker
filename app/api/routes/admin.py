from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.employee import Employee
from app.schemas.common import Page
from app.schemas.employee import EmployeeOut
from app.schemas.used_vacation_record import UsedVacationRecordOut
from app.schemas.vacation_allocation import VacationAllocationOut
from app.services.employee_import import import_employees_from_file
from app.services.employee_query import list_employees
from app.services.used_vacation_record_import import import_used_vacation_records_from_file
from app.services.used_vacation_record_query import list_used_vacation_records
from app.services.vacation_allocation_import import import_vacation_allocations_from_file
from app.services.vacation_allocation_query import list_vacation_allocations

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_IMPORT_EXTENSIONS = (".csv", ".xlsx", ".xls")


@router.post("/employees/import")
async def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    if not file.filename.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV or Excel files are supported"
        )

    content = await file.read()
    try:
        result = import_employees_from_file(content, file.filename, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "total_rows": result.total_rows,
        "imported": result.imported,
        "skipped_existing": result.skipped_existing,
    }


@router.post("/vacation-allocations/import")
async def import_vacation_allocations(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    if not file.filename.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV or Excel files are supported"
        )

    content = await file.read()
    try:
        result = import_vacation_allocations_from_file(content, file.filename, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "message": "Vacation days imported successfully",
        "total_records": result.total_records,
        "created": result.created,
        "updated": result.updated,
        "failed": result.failed,
        "errors": [
            {"row": e.row, "email": e.email, "reason": e.reason} for e in result.errors
        ],
    }


@router.post("/used-vacation-records/import")
async def import_used_vacation_records(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    if not file.filename.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV or Excel files are supported"
        )

    content = await file.read()
    try:
        result = import_used_vacation_records_from_file(content, file.filename, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "message": "Used vacation days imported successfully",
        "total_records": result.total_records,
        "created": result.created,
        "failed": result.failed,
        "errors": [
            {"row": e.row, "email": e.email, "reason": e.reason} for e in result.errors
        ],
    }


@router.get("/employees", response_model=Page[EmployeeOut])
def get_employees(
    email: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    items, total = list_employees(db, email=email, page=page, page_size=page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/vacation-allocations", response_model=Page[VacationAllocationOut])
def get_vacation_allocations(
    employee_id: int | None = None,
    year: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    items, total = list_vacation_allocations(
        db, employee_id=employee_id, year=year, page=page, page_size=page_size
    )
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/used-vacation-records", response_model=Page[UsedVacationRecordOut])
def get_used_vacation_records(
    employee_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="from_date must be before or equal to to_date"
        )

    items, total = list_used_vacation_records(
        db, employee_id=employee_id, from_date=from_date, to_date=to_date, page=page, page_size=page_size
    )
    return Page(items=items, total=total, page=page, page_size=page_size)

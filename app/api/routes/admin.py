from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.models.employee import Employee
from app.services.employee_import import import_employees_from_csv
from app.services.vacation_allocation_import import import_vacation_allocations_from_csv

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/employees/import")
async def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: Employee = Depends(get_current_admin),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

    content = await file.read()
    try:
        result = import_employees_from_csv(content, db)
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
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

    content = await file.read()
    try:
        result = import_vacation_allocations_from_csv(content, db)
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

from datetime import date

from sqlalchemy.orm import Session

from app.models.used_vacation_record import UsedVacationRecord


def list_used_vacation_records(
    db: Session,
    employee_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[UsedVacationRecord], int]:
    query = db.query(UsedVacationRecord)
    if employee_id is not None:
        query = query.filter(UsedVacationRecord.employee_id == employee_id)
    if from_date is not None:
        query = query.filter(UsedVacationRecord.end_date >= from_date)
    if to_date is not None:
        query = query.filter(UsedVacationRecord.start_date <= to_date)

    total = query.count()
    items = (
        query.order_by(UsedVacationRecord.employee_id, UsedVacationRecord.start_date)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total

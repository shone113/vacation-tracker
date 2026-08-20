from sqlalchemy.orm import Session, joinedload

from app.models.vacation_allocation import VacationAllocation


def list_vacation_allocations(
    db: Session,
    employee_id: int | None = None,
    year: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[VacationAllocation], int]:
    query = db.query(VacationAllocation).options(joinedload(VacationAllocation.employee))
    if employee_id is not None:
        query = query.filter(VacationAllocation.employee_id == employee_id)
    if year is not None:
        query = query.filter(VacationAllocation.year == year)

    total = query.count()
    items = (
        query.order_by(VacationAllocation.employee_id, VacationAllocation.year)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total

from sqlalchemy.orm import Session

from app.models.employee import Employee


def list_employees(
    db: Session, email: str | None = None, page: int = 1, page_size: int = 50
) -> tuple[list[Employee], int]:
    query = db.query(Employee)
    if email:
        query = query.filter(Employee.email.ilike(f"%{email}%"))

    total = query.count()
    items = (
        query.order_by(Employee.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.employee import Employee, EmployeeRole
from app.services.file_parsing import find_header_row, load_raw_grid

EXPECTED_HEADER = ["Employee Email", "Employee Password"]


@dataclass
class EmployeeImportResult:
    total_rows: int
    imported: int
    skipped_existing: int


def import_employees_from_file(content: bytes, filename: str, db: Session) -> EmployeeImportResult:
    grid = load_raw_grid(content, filename)
    header_index = find_header_row(grid, EXPECTED_HEADER)
    if header_index is None:
        raise ValueError(f"Could not find header row {EXPECTED_HEADER} in file")

    df = grid.iloc[header_index + 1 :, :2].copy()
    df.columns = ["email", "password"]
    df = df.dropna(how="all").reset_index(drop=True)

    df["email"] = df["email"].str.strip()
    df["password"] = df["password"].str.strip()
    df = df.dropna(subset=["email", "password"])

    total_rows = len(df)

    existing_emails = {
        email
        for (email,) in db.query(Employee.email)
        .filter(Employee.email.in_(df["email"].tolist()))
        .all()
    }

    new_employees = []
    seen_in_batch = set()
    for row in df.itertuples(index=False):
        if row.email in existing_emails or row.email in seen_in_batch:
            continue
        seen_in_batch.add(row.email)
        new_employees.append(
            Employee(
                email=row.email,
                hashed_password=hash_password(row.password),
                role=EmployeeRole.employee,
            )
        )

    db.add_all(new_employees)
    db.commit()

    return EmployeeImportResult(
        total_rows=total_rows,
        imported=len(new_employees),
        skipped_existing=total_rows - len(new_employees),
    )

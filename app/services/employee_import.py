import csv
import io
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.employee import Employee, EmployeeRole

EXPECTED_HEADER = ["Employee Email", "Employee Password"]


@dataclass
class EmployeeImportResult:
    total_rows: int
    imported: int
    skipped_existing: int


def _find_header_row_index(text: str) -> int:
    for i, row in enumerate(csv.reader(io.StringIO(text))):
        if [cell.strip() for cell in row] == EXPECTED_HEADER:
            return i
    raise ValueError(f"Could not find header row {EXPECTED_HEADER} in CSV")


def import_employees_from_csv(content: bytes, db: Session) -> EmployeeImportResult:
    text = content.decode("utf-8-sig")
    header_index = _find_header_row_index(text)

    lines = text.splitlines()
    csv_from_header = "\n".join(lines[header_index:])
    df = pd.read_csv(io.StringIO(csv_from_header), dtype=str)
    df = df.rename(columns={"Employee Email": "email", "Employee Password": "password"})

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

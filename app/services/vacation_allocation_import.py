from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.vacation_allocation import VacationAllocation
from app.services.file_parsing import load_raw_grid

EXPECTED_HEADER = ["Employee", "Total vacation days"]


@dataclass
class RowError:
    row: int
    email: str | None
    reason: str


@dataclass
class ParsedRow:
    row_number: int
    email: str
    total_days: int


@dataclass
class VacationAllocationImportResult:
    total_records: int
    created: int
    updated: int
    failed: int
    errors: list[RowError] = field(default_factory=list)


def _extract_year_and_header_index(grid: pd.DataFrame) -> tuple[int, int]:
    year = None
    header_index = None

    for i, row in grid.iterrows():
        cells = [str(c).strip() if pd.notna(c) else "" for c in row.tolist()]
        if year is None and len(cells) >= 2 and cells[0].lower() == "vacation year":
            try:
                year = int(cells[1])
            except ValueError:
                raise ValueError(f"Invalid year value in 'Vacation year' row: {cells[1]!r}")
            continue
        if cells[: len(EXPECTED_HEADER)] == EXPECTED_HEADER:
            header_index = i
            break

    if year is None:
        raise ValueError("Could not find 'Vacation year' row in file")
    if header_index is None:
        raise ValueError(f"Could not find header row {EXPECTED_HEADER} in file")

    return year, header_index


def _parse_total_days(raw: str) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        pass
    try:
        value = float(raw)
        if value.is_integer():
            return int(value)
    except (TypeError, ValueError):
        pass
    return None


def _validate_rows(df: pd.DataFrame) -> tuple[list[ParsedRow], list[RowError]]:
    parsed: list[ParsedRow] = []
    errors: list[RowError] = []

    for row_number, row in enumerate(df.itertuples(index=False), start=2):
        email = row.email.strip() if isinstance(row.email, str) else ""
        if not email:
            errors.append(RowError(row=row_number, email=None, reason="Missing employee email"))
            continue

        total_days = _parse_total_days(row.total_days_raw)
        if total_days is None or total_days < 0:
            errors.append(
                RowError(
                    row=row_number,
                    email=email,
                    reason=f"Invalid total vacation days value: {row.total_days_raw!r}",
                )
            )
            continue

        parsed.append(ParsedRow(row_number=row_number, email=email, total_days=total_days))

    return parsed, errors


def _validate_employees(
    rows: list[ParsedRow], db: Session
) -> tuple[list[ParsedRow], list[RowError], dict[str, int]]:
    emails = {r.email for r in rows}
    employee_id_by_email = {
        email: employee_id
        for employee_id, email in db.query(Employee.id, Employee.email)
        .filter(Employee.email.in_(emails))
        .all()
    }

    valid: list[ParsedRow] = []
    errors: list[RowError] = []
    for r in rows:
        if r.email not in employee_id_by_email:
            errors.append(RowError(row=r.row_number, email=r.email, reason="Employee not found"))
            continue
        valid.append(r)

    return valid, errors, employee_id_by_email


def _validate_duplicates(rows: list[ParsedRow]) -> tuple[list[ParsedRow], list[RowError]]:
    occurrences: dict[str, int] = {}
    for r in rows:
        occurrences[r.email] = occurrences.get(r.email, 0) + 1

    valid: list[ParsedRow] = []
    errors: list[RowError] = []
    for r in rows:
        if occurrences[r.email] > 1:
            errors.append(RowError(row=r.row_number, email=r.email, reason="Duplicate employee entry in file"))
        else:
            valid.append(r)

    return valid, errors


def _insert_or_update(
    rows: list[ParsedRow], employee_id_by_email: dict[str, int], year: int, db: Session
) -> tuple[int, int]:
    if not rows:
        return 0, 0

    employee_ids = [employee_id_by_email[r.email] for r in rows]
    existing_by_employee_id = {
        allocation.employee_id: allocation
        for allocation in db.query(VacationAllocation)
        .filter(VacationAllocation.employee_id.in_(employee_ids), VacationAllocation.year == year)
        .all()
    }

    created = 0
    updated = 0
    for r in rows:
        employee_id = employee_id_by_email[r.email]
        allocation = existing_by_employee_id.get(employee_id)
        if allocation:
            allocation.total_days = r.total_days
            updated += 1
        else:
            db.add(VacationAllocation(employee_id=employee_id, year=year, total_days=r.total_days))
            created += 1

    db.commit()
    return created, updated


def import_vacation_allocations_from_file(
    content: bytes, filename: str, db: Session
) -> VacationAllocationImportResult:
    grid = load_raw_grid(content, filename)
    year, header_index = _extract_year_and_header_index(grid)

    df = grid.iloc[header_index + 1 :, :2].copy()
    df.columns = ["email", "total_days_raw"]
    df = df.dropna(how="all").reset_index(drop=True)

    total_records = len(df)

    rows, row_errors = _validate_rows(df)
    rows, employee_errors, employee_id_by_email = _validate_employees(rows, db)
    rows, duplicate_errors = _validate_duplicates(rows)

    created, updated = _insert_or_update(rows, employee_id_by_email, year, db)

    errors = row_errors + employee_errors + duplicate_errors

    return VacationAllocationImportResult(
        total_records=total_records,
        created=created,
        updated=updated,
        failed=len(errors),
        errors=errors,
    )

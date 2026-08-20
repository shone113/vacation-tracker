import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.used_vacation_record import UsedVacationRecord
from app.services.date_ranges import periods_overlap
from app.services.file_parsing import load_raw_grid

EXPECTED_COLUMNS = ["Employee", "Vacation start date", "Vacation end date"]

_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}
_WEEKDAYS = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}
_DATE_PATTERN = re.compile(
    r"^(?P<weekday>[A-Za-z]+),\s*(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})$"
)


@dataclass
class RowError:
    row: int
    email: str | None
    reason: str


@dataclass
class ParsedRow:
    row_number: int
    email: str
    start_date: date
    end_date: date


@dataclass
class UsedVacationRecordImportResult:
    total_records: int
    created: int
    failed: int
    errors: list[RowError] = field(default_factory=list)


def _parse_date(raw: str) -> date | None:
    if not isinstance(raw, str):
        return None

    match = _DATE_PATTERN.match(raw.strip())
    if not match:
        return None

    month = _MONTHS.get(match.group("month"))
    expected_weekday = _WEEKDAYS.get(match.group("weekday"))
    if month is None or expected_weekday is None:
        return None

    try:
        parsed = date(int(match.group("year")), month, int(match.group("day")))
    except ValueError:
        return None

    if parsed.weekday() != expected_weekday:
        return None

    return parsed


def _validate_rows(df: pd.DataFrame) -> tuple[list[ParsedRow], list[RowError]]:
    parsed: list[ParsedRow] = []
    errors: list[RowError] = []

    for row_number, row in enumerate(df.itertuples(index=False), start=2):
        email = row.email.strip() if isinstance(row.email, str) else ""
        if not email:
            errors.append(RowError(row=row_number, email=None, reason="Missing employee email"))
            continue

        start_date = _parse_date(row.start_date_raw)
        if start_date is None:
            errors.append(
                RowError(row=row_number, email=email, reason=f"Invalid start date value: {row.start_date_raw!r}")
            )
            continue

        end_date = _parse_date(row.end_date_raw)
        if end_date is None:
            errors.append(
                RowError(row=row_number, email=email, reason=f"Invalid end date value: {row.end_date_raw!r}")
            )
            continue

        if end_date < start_date:
            errors.append(
                RowError(
                    row=row_number,
                    email=email,
                    reason=f"End date {end_date.isoformat()} is before start date {start_date.isoformat()}",
                )
            )
            continue

        parsed.append(ParsedRow(row_number=row_number, email=email, start_date=start_date, end_date=end_date))

    return parsed, errors


def _validate_employees(
    rows: list[ParsedRow], db: Session
) -> tuple[list[ParsedRow], list[RowError], dict[str, int]]:
    if not rows:
        return [], [], {}

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


def _validate_overlaps(
    rows: list[ParsedRow], employee_id_by_email: dict[str, int], db: Session
) -> tuple[list[ParsedRow], list[RowError]]:
    if not rows:
        return [], []

    employee_ids = {employee_id_by_email[r.email] for r in rows}

    existing_periods: dict[int, list[tuple[date, date]]] = defaultdict(list)
    for employee_id, start_date, end_date in (
        db.query(UsedVacationRecord.employee_id, UsedVacationRecord.start_date, UsedVacationRecord.end_date)
        .filter(UsedVacationRecord.employee_id.in_(employee_ids))
        .all()
    ):
        existing_periods[employee_id].append((start_date, end_date))

    accepted_periods: dict[int, list[tuple[date, date]]] = defaultdict(list)
    valid: list[ParsedRow] = []
    errors: list[RowError] = []

    for r in rows:
        employee_id = employee_id_by_email[r.email]
        conflict = next(
            (
                period
                for period in existing_periods[employee_id] + accepted_periods[employee_id]
                if periods_overlap(r.start_date, r.end_date, period[0], period[1])
            ),
            None,
        )
        if conflict:
            errors.append(
                RowError(
                    row=r.row_number,
                    email=r.email,
                    reason=f"Overlaps existing period {conflict[0].isoformat()} to {conflict[1].isoformat()}",
                )
            )
            continue

        accepted_periods[employee_id].append((r.start_date, r.end_date))
        valid.append(r)

    return valid, errors


def import_used_vacation_records_from_file(
    content: bytes, filename: str, db: Session
) -> UsedVacationRecordImportResult:
    grid = load_raw_grid(content, filename)

    header_row = [str(c).strip() if pd.notna(c) else "" for c in grid.iloc[0].tolist()]
    if header_row[: len(EXPECTED_COLUMNS)] != EXPECTED_COLUMNS:
        raise ValueError(f"Missing expected columns in file: {EXPECTED_COLUMNS}")

    df = grid.iloc[1:, : len(EXPECTED_COLUMNS)].copy()
    df.columns = ["email", "start_date_raw", "end_date_raw"]
    df = df.dropna(how="all").reset_index(drop=True)

    total_records = len(df)

    rows, row_errors = _validate_rows(df)
    rows, employee_errors, employee_id_by_email = _validate_employees(rows, db)
    rows, overlap_errors = _validate_overlaps(rows, employee_id_by_email, db)

    db.add_all(
        UsedVacationRecord(
            employee_id=employee_id_by_email[r.email],
            start_date=r.start_date,
            end_date=r.end_date,
        )
        for r in rows
    )
    db.commit()

    errors = row_errors + employee_errors + overlap_errors

    return UsedVacationRecordImportResult(
        total_records=total_records,
        created=len(rows),
        failed=len(errors),
        errors=errors,
    )

from app.services.used_vacation_record_import import import_used_vacation_records_from_csv


def _csv(*rows):
    return ("Employee,Vacation start date,Vacation end date\n" + "\n".join(rows)).encode()


def test_imports_valid_record(db, make_employee):
    make_employee("user1@test.local", "x")
    content = _csv('user1@test.local,"Monday, August 3, 2020","Friday, August 7, 2020"')
    result = import_used_vacation_records_from_csv(content, db)
    assert result.created == 1
    assert result.failed == 0


def test_weekday_mismatch_fails_row(db, make_employee):
    make_employee("user1@test.local", "x")
    # August 3, 2020 is actually a Monday, not a Tuesday
    content = _csv('user1@test.local,"Tuesday, August 3, 2020","Tuesday, August 3, 2020"')
    result = import_used_vacation_records_from_csv(content, db)
    assert result.failed == 1


def test_overlapping_periods_in_file_second_one_rejected(db, make_employee):
    make_employee("user1@test.local", "x")
    content = _csv(
        'user1@test.local,"Monday, August 3, 2020","Friday, August 7, 2020"',
        'user1@test.local,"Wednesday, August 5, 2020","Wednesday, August 12, 2020"',
    )
    result = import_used_vacation_records_from_csv(content, db)
    assert result.created == 1
    assert result.failed == 1
    assert "Overlaps" in result.errors[0].reason

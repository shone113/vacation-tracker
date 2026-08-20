from datetime import date

from app.services.date_ranges import periods_overlap, weekdays_in_range, weekdays_in_year


def test_overlapping_periods():
    assert periods_overlap(date(2020, 8, 1), date(2020, 8, 5), date(2020, 8, 3), date(2020, 8, 10)) is True


def test_weekdays_excludes_weekend():
    assert weekdays_in_range(date(2020, 8, 7), date(2020, 8, 10)) == 2  # Fri..Mon, skip Sat/Sun


def test_weekdays_split_across_year_boundary():
    # Mon 2020-12-28 .. Wed 2021-01-06
    assert weekdays_in_year(date(2020, 12, 28), date(2021, 1, 6), 2020) == 4
    assert weekdays_in_year(date(2020, 12, 28), date(2021, 1, 6), 2021) == 4

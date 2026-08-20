from datetime import date, timedelta


def periods_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def weekdays_in_range(start: date, end: date) -> int:
    days = (end - start).days + 1
    return sum(1 for i in range(days) if (start + timedelta(days=i)).weekday() < 5)


def weekdays_in_year(start: date, end: date, year: int) -> int:
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    intersection_start = max(start, year_start)
    intersection_end = min(end, year_end)
    if intersection_start > intersection_end:
        return 0

    return weekdays_in_range(intersection_start, intersection_end)

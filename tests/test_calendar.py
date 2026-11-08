from datetime import date

from utils.calendar import (
    format_week_range,
    monday_of,
    week_dates,
    weekday_full,
    weekday_short,
)


def test_sunday_belongs_to_week_starting_monday() -> None:
    sunday = date(2026, 11, 8)
    monday = monday_of(sunday)
    days = week_dates(monday)
    assert monday == date(2026, 11, 2)
    assert days[0] == date(2026, 11, 2)
    assert days[-1] == sunday
    assert weekday_full(sunday) == "Chủ Nhật"
    assert weekday_short(monday) == "T2"
    assert format_week_range(monday) == "02/11 – 08/11/2026"

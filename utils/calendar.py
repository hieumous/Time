from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

WEEKDAYS_FULL = (
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
)
WEEKDAYS_SHORT = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")

SESSIONS: tuple[dict[str, str], ...] = (
    {
        "id": "morning",
        "label": "Buổi sáng",
        "hours": "05:00 – 12:00",
        "icon": ":material/wb_sunny:",
    },
    {
        "id": "afternoon",
        "label": "Buổi chiều",
        "hours": "12:00 – 18:00",
        "icon": ":material/wb_twilight:",
    },
    {
        "id": "evening",
        "label": "Buổi tối",
        "hours": "18:00 – 23:00",
        "icon": ":material/dark_mode:",
    },
)

SESSION_BY_ID = {session["id"]: session for session in SESSIONS}


def today_vn() -> date:
    return datetime.now(VN_TZ).date()


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def week_dates(monday: date) -> list[date]:
    return [monday + timedelta(days=offset) for offset in range(7)]


def weekday_full(day: date) -> str:
    return WEEKDAYS_FULL[day.weekday()]


def weekday_short(day: date) -> str:
    return WEEKDAYS_SHORT[day.weekday()]


def format_date(day: date) -> str:
    return day.strftime("%d/%m/%Y")


def format_date_short(day: date) -> str:
    return day.strftime("%d/%m")


def format_week_range(monday: date) -> str:
    sunday = monday + timedelta(days=6)
    return f"{format_date_short(monday)} – {format_date(sunday)}"


def day_tab_label(day: date, today: date | None = None) -> str:
    label = f"{weekday_short(day)} {format_date_short(day)}"
    if today is not None and day == today:
        return f"{label} · hôm nay"
    return label


def iso(day: date) -> str:
    return day.isoformat()

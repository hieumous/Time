from __future__ import annotations

from datetime import date
from io import BytesIO

from openpyxl import Workbook

from utils.calendar import (
    SESSIONS,
    SESSION_BY_ID,
    format_date,
    today_vn,
    weekday_full,
)
from utils.storage import Task, load_session_notes, parse_session_note_key

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def excel_filename(prefix: str = "quan-ly-thoi-gian") -> str:
    return f"{prefix}_{today_vn().isoformat()}.xlsx"


def _notes_map(notes: dict[str, str] | None) -> dict[str, str]:
    if notes is None:
        return load_session_notes()
    return notes


def _session_note(notes: dict[str, str], day: date, session_id: str) -> str:
    return str(notes.get(f"{day.isoformat()}:{session_id}", ""))


def _task_rows(tasks: list[Task], notes: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for task in sorted(tasks, key=lambda item: (item.date, item.session, item.created_at)):
        day = date.fromisoformat(task.date)
        session = SESSION_BY_ID[task.session]
        rows.append(
            {
                "Ngày": format_date(day),
                "Thứ": weekday_full(day),
                "Buổi": session["label"],
                "Khung giờ": session["hours"],
                "Việc": task.text,
                "Trạng thái": "Đã xong" if task.done else "Cần làm",
                "Ghi chú việc": task.note,
                "Ghi chú buổi": _session_note(notes, day, task.session),
                "Tạo lúc": task.created_at,
                "Xong lúc": task.done_at or "",
            }
        )
    return rows


def _note_rows(
    tasks: list[Task],
    notes: dict[str, str],
    week_days: list[date] | None = None,
) -> list[dict[str, str]]:
    if week_days is not None:
        allowed_days = {day.isoformat() for day in week_days}
    else:
        allowed_days = {task.date for task in tasks}
    rows: list[dict[str, str]] = []
    for key, value in sorted(notes.items()):
        parsed = parse_session_note_key(key)
        if parsed is None or not value.strip():
            continue
        day, session_id = parsed
        if allowed_days and day.isoformat() not in allowed_days:
            continue
        session = SESSION_BY_ID[session_id]
        rows.append(
            {
                "Ngày": format_date(day),
                "Thứ": weekday_full(day),
                "Buổi": session["label"],
                "Khung giờ": session["hours"],
                "Ghi chú buổi": value,
            }
        )
    return rows


def _week_grid_rows(days: list[date], tasks: list[Task], notes: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for day in days:
        row: dict[str, str] = {
            "Ngày": format_date(day),
            "Thứ": weekday_full(day),
        }
        for session in SESSIONS:
            day_tasks = [
                task
                for task in tasks
                if task.date == day.isoformat() and task.session == session["id"]
            ]
            lines = []
            for task in day_tasks:
                mark = "xong" if task.done else "cần làm"
                line = f"[{mark}] {task.text}"
                if task.note:
                    line += f" — {task.note}"
                lines.append(line)
            session_note = _session_note(notes, day, session["id"])
            if session_note:
                lines.append(f"Ghi chú: {session_note}")
            row[session["label"]] = "\n".join(lines)
        rows.append(row)
    return rows


def _write_sheet(book: Workbook, title: str, rows: list[dict[str, str]], columns: list[str]) -> None:
    sheet = book.create_sheet(title)
    sheet.append(columns)
    for row in rows:
        sheet.append([row.get(column, "") for column in columns])
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        width = 14
        for cell in column:
            if cell.value:
                width = max(width, min(48, len(str(cell.value).split("\n", 1)[0]) + 2))
        sheet.column_dimensions[column[0].column_letter].width = width


def build_excel_bytes(
    tasks: list[Task],
    *,
    week_days: list[date] | None = None,
    notes: dict[str, str] | None = None,
) -> bytes:
    note_map = _notes_map(notes)
    book = Workbook()
    default_sheet = book.active
    book.remove(default_sheet)
    _write_sheet(
        book,
        "Việc",
        _task_rows(tasks, note_map),
        [
            "Ngày",
            "Thứ",
            "Buổi",
            "Khung giờ",
            "Việc",
            "Trạng thái",
            "Ghi chú việc",
            "Ghi chú buổi",
            "Tạo lúc",
            "Xong lúc",
        ],
    )
    _write_sheet(
        book,
        "Ghi chú buổi",
        _note_rows(tasks, note_map, week_days),
        ["Ngày", "Thứ", "Buổi", "Khung giờ", "Ghi chú buổi"],
    )
    if week_days:
        _write_sheet(
            book,
            "Lịch tuần",
            _week_grid_rows(week_days, tasks, note_map),
            ["Ngày", "Thứ", *(session["label"] for session in SESSIONS)],
        )
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()

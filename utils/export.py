from __future__ import annotations

from datetime import date
from io import BytesIO

import pandas as pd

from utils.calendar import (
    SESSIONS,
    SESSION_BY_ID,
    format_date,
    today_vn,
    weekday_full,
)
from utils.storage import Task, get_session_note, load_session_notes, parse_session_note_key

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def excel_filename(prefix: str = "quan-ly-thoi-gian") -> str:
    return f"{prefix}_{today_vn().isoformat()}.xlsx"


def _task_rows(tasks: list[Task]) -> list[dict[str, str]]:
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
                "Ghi chú buổi": get_session_note(day, task.session),
                "Tạo lúc": task.created_at,
                "Xong lúc": task.done_at or "",
            }
        )
    return rows


def _note_rows(tasks: list[Task], week_days: list[date] | None = None) -> list[dict[str, str]]:
    notes = load_session_notes()
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


def _week_grid_rows(days: list[date], tasks: list[Task]) -> list[dict[str, str]]:
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
            session_note = get_session_note(day, session["id"])
            if session_note:
                lines.append(f"Ghi chú: {session_note}")
            row[session["label"]] = "\n".join(lines)
        rows.append(row)
    return rows


def build_excel_bytes(
    tasks: list[Task],
    *,
    week_days: list[date] | None = None,
) -> bytes:
    task_df = pd.DataFrame(
        _task_rows(tasks),
        columns=[
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
    note_df = pd.DataFrame(
        _note_rows(tasks, week_days),
        columns=["Ngày", "Thứ", "Buổi", "Khung giờ", "Ghi chú buổi"],
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        task_df.to_excel(writer, index=False, sheet_name="Việc")
        note_df.to_excel(writer, index=False, sheet_name="Ghi chú buổi")
        if week_days:
            grid_df = pd.DataFrame(
                _week_grid_rows(week_days, tasks),
                columns=["Ngày", "Thứ", *(session["label"] for session in SESSIONS)],
            )
            grid_df.to_excel(writer, index=False, sheet_name="Lịch tuần")
        for sheet in writer.sheets.values():
            sheet.freeze_panes = "A2"
            for column in sheet.columns:
                width = 14
                for cell in column:
                    if cell.value:
                        width = max(width, min(48, len(str(cell.value).split("\n", 1)[0]) + 2))
                sheet.column_dimensions[column[0].column_letter].width = width
    return buffer.getvalue()

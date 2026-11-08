from __future__ import annotations

from datetime import date

import streamlit as st

from utils.calendar import (
    SESSIONS,
    SESSION_BY_ID,
    format_date,
    today_vn,
    weekday_full,
    week_dates,
)
from utils.storage import Task, load_session_notes, load_tasks, parse_session_note_key
from utils.ui import (
    render_excel_download,
    render_open_dialog,
    render_session_note,
    render_task_row,
)

today = today_vn()
monday: date = st.session_state.week_monday
sunday = week_dates(monday)[-1]
all_tasks = load_tasks()

st.caption("Lọc mọi việc đã ghi theo tuần, buổi, trạng thái hoặc từ khóa.")

filters = st.container(horizontal=True, vertical_alignment="bottom")
with filters:
    scope = st.segmented_control(
        "Phạm vi",
        options=["week", "all"],
        default="week",
        format_func=lambda value: "Tuần đang xem" if value == "week" else "Mọi tuần",
        key="task_scope",
        required=True,
    )
    status = st.segmented_control(
        "Trạng thái",
        options=["all", "todo", "done"],
        default="all",
        format_func=lambda value: {
            "all": "Tất cả",
            "todo": "Cần làm",
            "done": "Đã xong",
        }[value],
        key="task_status",
        required=True,
    )
    session_filter = st.pills(
        "Buổi",
        options=["all", *(session["id"] for session in SESSIONS)],
        default="all",
        format_func=lambda value: "Mọi buổi"
        if value == "all"
        else SESSION_BY_ID[value]["label"],
        key="task_session",
        selection_mode="single",
        required=True,
    )
    query = st.text_input(
        "Tìm việc",
        placeholder="Nhập từ khóa…",
        key="task_query",
    )

filtered: list[Task] = []
query_text = query.strip().casefold()
session_value = session_filter or "all"
for task in all_tasks:
    task_day = date.fromisoformat(task.date)
    if scope == "week" and not (monday <= task_day <= sunday):
        continue
    if status == "todo" and task.done:
        continue
    if status == "done" and not task.done:
        continue
    if session_value != "all" and task.session != session_value:
        continue
    if query_text and query_text not in task.text.casefold() and query_text not in task.note.casefold():
        continue
    filtered.append(task)

filtered.sort(key=lambda task: (task.date, task.session, task.created_at))

st.caption(f"{len(filtered)} việc khớp bộ lọc.")

grouped: dict[str, list[Task]] = {}
for task in filtered:
    grouped.setdefault(task.date, []).append(task)

session_notes = load_session_notes()
for note_key, note_text in session_notes.items():
    parsed = parse_session_note_key(note_key)
    if parsed is None or not note_text.strip():
        continue
    note_day, note_session = parsed
    if scope == "week" and not (monday <= note_day <= sunday):
        continue
    if session_value != "all" and note_session != session_value:
        continue
    if query_text and query_text not in note_text.casefold():
        if note_day.isoformat() not in grouped:
            continue
    grouped.setdefault(note_day.isoformat(), [])

export_days = [date.fromisoformat(day_key) for day_key in sorted(grouped)]
render_excel_download(
    filtered,
    key="export_tasks_excel",
    week_days=export_days or None,
    label="Xuất Excel",
)

if not grouped:
    st.info(
        "Thử đổi bộ lọc, hoặc mở Lịch tuần để thêm việc cho một buổi.",
        icon=":material/search:",
        title="Không có việc nào",
    )
else:
    for day_key in sorted(grouped):
        day = date.fromisoformat(day_key)
        day_tasks = grouped[day_key]
        label = f"{weekday_full(day)}, {format_date(day)}"
        if day == today:
            label += " · hôm nay"
        with st.container(border=True):
            st.subheader(label)
            for session in SESSIONS:
                session_tasks = [task for task in day_tasks if task.session == session["id"]]
                session_note = session_notes.get(f"{day_key}:{session['id']}", "")
                if not session_tasks and not session_note.strip():
                    continue
                if session_value != "all" and session["id"] != session_value:
                    continue
                st.markdown(f"{session['icon']} **{session['label']}** · {session['hours']}")
                render_session_note(day, session["id"], key_prefix="all_")
                for task in session_tasks:
                    render_task_row(task, key_prefix="all_")

render_open_dialog()

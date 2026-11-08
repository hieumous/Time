from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from utils.calendar import (
    SESSIONS,
    day_tab_label,
    format_date,
    format_week_range,
    monday_of,
    today_vn,
    week_dates,
    weekday_full,
)
from utils.storage import (
    Task,
    add_task,
    tasks_for,
    tasks_in_range,
)
from utils.ui import render_excel_download, render_open_dialog, render_session_note, render_task_row

today = today_vn()
monday: date = st.session_state.week_monday
days = week_dates(monday)
sunday = days[-1]
week_tasks = tasks_in_range(monday, sunday)
done_count = sum(1 for task in week_tasks if task.done)
todo_count = len(week_tasks) - done_count
is_this_week = monday == monday_of(today)


def _shift_week(delta_weeks: int) -> None:
    new_monday = st.session_state.week_monday + timedelta(weeks=delta_weeks)
    st.session_state.week_monday = new_monday
    st.session_state.jump_date = new_monday


def _go_this_week() -> None:
    st.session_state.week_monday = monday_of(today)
    st.session_state.jump_date = today


def _jump_to_picked_date() -> None:
    picked = st.session_state.jump_date
    st.session_state.week_monday = monday_of(picked)


st.caption(
    "Mỗi ô là một buổi trong ngày. Tích việc đã xong, để trống việc còn phải làm. "
    "Ngày trên tab luôn đúng với lịch."
)

nav = st.container(horizontal=True, vertical_alignment="bottom", gap="small")
with nav:
    st.button(
        "Tuần trước",
        icon=":material/chevron_left:",
        key="prev_week",
        on_click=_shift_week,
        args=(-1,),
    )
    st.button(
        "Tuần này",
        icon=":material/today:",
        key="this_week",
        type="primary" if is_this_week else "secondary",
        on_click=_go_this_week,
        disabled=is_this_week,
    )
    st.button(
        "Tuần sau",
        icon=":material/chevron_right:",
        key="next_week",
        on_click=_shift_week,
        args=(1,),
        icon_position="right",
    )
    if "jump_date" not in st.session_state:
        st.session_state.jump_date = today if is_this_week else monday
    st.date_input(
        "Nhảy tới ngày",
        format="DD/MM/YYYY",
        key="jump_date",
        on_change=_jump_to_picked_date,
        help="Chọn một ngày bất kỳ để mở đúng tuần chứa ngày đó.",
    )

st.subheader(f"Tuần {format_week_range(monday)}")
if is_this_week:
    st.badge("Đang xem tuần này", icon=":material/today:", color="green")
else:
    st.badge("Tuần khác", icon=":material/event_note:", color="gray")

metric_cols = st.columns(3)
metric_cols[0].metric("Cần làm", todo_count, border=True, icon=":material/pending_actions:")
metric_cols[1].metric("Đã xong", done_count, border=True, icon=":material/task_alt:")
metric_cols[2].metric(
    "Tổng việc tuần",
    len(week_tasks),
    border=True,
    icon=":material/assignment:",
)
render_excel_download(
    week_tasks,
    key="export_week_excel",
    week_days=days,
    label="Xuất Excel tuần này",
)


def _counts_for_day(day: date) -> tuple[int, int]:
    day_tasks = [task for task in week_tasks if task.date == day.isoformat()]
    finished = sum(1 for task in day_tasks if task.done)
    return finished, len(day_tasks)


labels = [day_tab_label(day, today) for day in days]
default_label = day_tab_label(today, today) if is_this_week else labels[0]
if st.session_state.get("week_day_tabs") not in labels:
    st.session_state.week_day_tabs = default_label

tabs = st.tabs(labels, default=default_label, key="week_day_tabs", on_change="rerun")


def _render_session(day: date, session: dict[str, str], session_tasks: list[Task]) -> None:
    finished = sum(1 for task in session_tasks if task.done)
    st.markdown(f"{session['icon']} **{session['label']}**")
    st.caption(session["hours"])
    if session_tasks:
        color = "green" if finished == len(session_tasks) else "orange"
        st.badge(
            f"{finished}/{len(session_tasks)} xong",
            icon=":material/check_circle:",
            color=color,
        )
    else:
        st.badge("Chưa có việc", icon=":material/notes:", color="gray")

    render_session_note(day, session["id"], key_prefix="week_")
    if not session_tasks:
        st.caption("Ghi việc cần làm hoặc việc đã làm được trong buổi này.")
    for task in session_tasks:
        render_task_row(task)

    with st.form(f"add_{day.isoformat()}_{session['id']}", clear_on_submit=True, border=False):
        new_text = st.text_input(
            "Thêm việc",
            placeholder="Ví dụ: Họp team 9h, hoàn thành báo cáo…",
            max_chars=200,
            key=f"new_task_{day.isoformat()}_{session['id']}",
        )
        new_note = st.text_area(
            "Ghi chú việc mới",
            placeholder="Ghi chú kèm việc này (không bắt buộc)…",
            height=70,
            key=f"new_note_{day.isoformat()}_{session['id']}",
        )
        submitted = st.form_submit_button(
            "Thêm việc",
            icon=":material/add:",
            type="primary",
            width="stretch",
        )
        if submitted:
            try:
                add_task(day, session["id"], new_text, new_note)
            except ValueError as error:
                st.warning(str(error))
            else:
                st.rerun()


for tab, day in zip(tabs, days):
    if not tab.open:
        continue
    with tab:
        day_done, day_total = _counts_for_day(day)
        heading = f"{weekday_full(day)}, {format_date(day)}"
        st.header(heading)
        if day == today:
            st.badge("Hôm nay", icon=":material/today:", color="blue")
        elif day < today:
            st.badge("Đã qua", icon=":material/history:", color="gray")
        else:
            st.badge("Sắp tới", icon=":material/event_upcoming:", color="violet")
        if day_total:
            st.caption(f"{day_done}/{day_total} việc đã xong trong ngày này.")
        else:
            st.caption("Chưa có việc nào. Thêm việc vào từng buổi bên dưới.")

        session_cols = st.columns(3)
        for column, session in zip(session_cols, SESSIONS):
            with column.container(border=True, height="stretch"):
                _render_session(day, session, tasks_for(day, session["id"]))

render_open_dialog()

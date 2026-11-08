from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.calendar import (
    SESSION_BY_ID,
    format_date,
    format_week_range,
    today_vn,
    week_dates,
    weekday_short,
)
from utils.storage import tasks_in_range
from utils.ui import render_excel_download

today = today_vn()
monday: date = st.session_state.week_monday
days = week_dates(monday)
sunday = days[-1]
week_tasks = tasks_in_range(monday, sunday)

st.caption(f"Tiến độ tuần {format_week_range(monday)}. Đánh dấu xong ở Lịch tuần hoặc Tất cả việc.")
render_excel_download(
    week_tasks,
    key="export_overview_excel",
    week_days=days,
    label="Xuất Excel tuần này",
)

done_tasks = [task for task in week_tasks if task.done]
todo_tasks = [task for task in week_tasks if not task.done]
progress = 0 if not week_tasks else round(100 * len(done_tasks) / len(week_tasks))

metric_cols = st.columns(4)
metric_cols[0].metric("Việc trong tuần", len(week_tasks), border=True, icon=":material/assignment:")
metric_cols[1].metric("Cần làm", len(todo_tasks), border=True, icon=":material/pending_actions:")
metric_cols[2].metric("Đã xong", len(done_tasks), border=True, icon=":material/task_alt:")
metric_cols[3].metric("Hoàn thành", f"{progress}%", border=True, icon=":material/trending_up:")

rows = []
for day in days:
    day_tasks = [task for task in week_tasks if task.date == day.isoformat()]
    rows.append(
        {
            "Thứ": weekday_short(day),
            "Ngày": format_date(day),
            "Cần làm": sum(1 for task in day_tasks if not task.done),
            "Đã xong": sum(1 for task in day_tasks if task.done),
        }
    )
chart_df = pd.DataFrame(rows)

st.subheader("Việc theo ngày")
st.bar_chart(
    chart_df,
    x="Thứ",
    y=["Cần làm", "Đã xong"],
    color=["#EA580C", "#059669"],
    stack=True,
    sort=False,
    alt="Số việc cần làm và đã xong theo từng thứ trong tuần đang xem",
)
st.dataframe(
    chart_df,
    hide_index=True,
    alt="Bảng số việc cần làm và đã xong theo ngày trong tuần",
)

left, right = st.columns(2)
with left.container(border=True, height="stretch"):
    st.subheader("Cần làm")
    if not todo_tasks:
        st.success("Không còn việc chưa xong trong tuần này.", icon=":material/check_circle:")
    else:
        for task in sorted(todo_tasks, key=lambda item: (item.date, item.session)):
            day = date.fromisoformat(task.date)
            session = SESSION_BY_ID[task.session]
            mark = "Hôm nay · " if day == today else ""
            extra = f" — {task.note}" if task.note else ""
            st.markdown(
                f"- {mark}**{weekday_short(day)} {format_date(day)}** · "
                f"{session['label']}: {task.text}{extra}"
            )

with right.container(border=True, height="stretch"):
    st.subheader("Đã làm được")
    if not done_tasks:
        st.info("Chưa có việc nào được đánh dấu xong.", icon=":material/info:")
    else:
        for task in sorted(done_tasks, key=lambda item: (item.date, item.session)):
            day = date.fromisoformat(task.date)
            session = SESSION_BY_ID[task.session]
            extra = f" — {task.note}" if task.note else ""
            st.markdown(
                f"- **{weekday_short(day)} {format_date(day)}** · "
                f"{session['label']}: ~~{task.text}~~{extra}"
            )

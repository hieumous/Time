from __future__ import annotations

import streamlit as st

from utils.calendar import monday_of, today_vn
from utils.ui import init_planner_state

st.set_page_config(
    page_title="Quản lý thời gian",
    page_icon=":material/calendar_month:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_planner_state()
st.session_state.setdefault("week_monday", monday_of(today_vn()))

page = st.navigation(
    [
        st.Page(
            "app_pages/week.py",
            title="Lịch tuần",
            icon=":material/calendar_view_week:",
            default=True,
            help=(
                "Xem tuần từ Thứ Hai đến Chủ Nhật, mỗi ngày có buổi sáng, "
                "chiều và tối. Ghi việc cần làm hoặc đã xong đúng ngày."
            ),
        ),
        st.Page(
            "app_pages/tasks.py",
            title="Tất cả việc",
            icon=":material/checklist:",
            help=(
                "Tìm và lọc mọi việc đã ghi. Đánh dấu xong, sửa hoặc xóa "
                "mà không cần mở từng ngày."
            ),
        ),
        st.Page(
            "app_pages/overview.py",
            title="Tổng quan",
            icon=":material/analytics:",
            help=(
                "Nhìn tiến độ tuần đang chọn: việc còn lại, việc đã xong "
                "và thống kê theo từng ngày."
            ),
        ),
    ],
    position="top",
)

st.title(page.title, icon=page.icon)
page.run()

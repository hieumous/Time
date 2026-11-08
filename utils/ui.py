from __future__ import annotations

from datetime import date

import streamlit as st

from utils.calendar import SESSIONS, SESSION_BY_ID, format_date, weekday_full
from utils.storage import Task, delete_task, get_session_note, save_session_note, set_done, update_task
from utils.export import EXCEL_MIME, build_excel_bytes, excel_filename


def escape_markdown(text: str) -> str:
    specials = "\\`*_{}[]()#+-.!|"
    escaped = []
    for char in text:
        if char in specials:
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)


def init_planner_state() -> None:
    st.session_state.setdefault("edit_task_id", None)
    st.session_state.setdefault("delete_task_id", None)


def clear_task_dialogs() -> None:
    st.session_state.edit_task_id = None
    st.session_state.delete_task_id = None


def open_edit_dialog(task_id: str) -> None:
    st.session_state.edit_task_id = task_id
    st.session_state.delete_task_id = None


def open_delete_dialog(task_id: str) -> None:
    st.session_state.delete_task_id = task_id
    st.session_state.edit_task_id = None


def _toggle_done(task_id: str, widget_key: str) -> None:
    set_done(task_id, bool(st.session_state.get(widget_key, False)))


def _save_task_note(task_id: str, widget_key: str) -> None:
    update_task(task_id, note=str(st.session_state.get(widget_key, "")))


def _save_session_note(day: date, session_id: str, widget_key: str) -> None:
    save_session_note(day, session_id, str(st.session_state.get(widget_key, "")))


def render_session_note(day: date, session_id: str, *, key_prefix: str = "") -> None:
    widget_key = f"{key_prefix}session_note_{day.isoformat()}_{session_id}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = get_session_note(day, session_id)
    st.text_area(
        "Ghi chú buổi",
        placeholder="Ghi chú ngay tại đây: cần làm gì, đã làm được gì…",
        height=80,
        key=widget_key,
        on_change=_save_session_note,
        args=(day, session_id, widget_key),
        help="Tự lưu khi bạn rời ô ghi chú.",
    )


def render_excel_download(
    tasks: list[Task],
    *,
    key: str,
    week_days: list[date] | None = None,
    label: str = "Xuất Excel",
) -> None:
    def _make_file() -> bytes:
        return build_excel_bytes(tasks, week_days=week_days)

    st.download_button(
        label,
        data=_make_file,
        file_name=excel_filename(),
        mime=EXCEL_MIME,
        icon=":material/download:",
        key=key,
        on_click="ignore",
        help="Tải file .xlsx gồm việc, ghi chú buổi và trạng thái.",
    )


@st.dialog("Sửa việc", icon=":material/edit_note:", on_dismiss=clear_task_dialogs)
def edit_task_dialog(task: Task) -> None:
    session_ids = [session["id"] for session in SESSIONS]
    default_index = session_ids.index(task.session) if task.session in session_ids else 0
    text = st.text_input("Việc cần làm", value=task.text, max_chars=200)
    note = st.text_area("Ghi chú thêm", value=task.note, height=80)
    session = st.segmented_control(
        "Buổi",
        options=session_ids,
        default=session_ids[default_index],
        format_func=lambda session_id: SESSION_BY_ID[session_id]["label"],
        key=f"edit_session_{task.id}",
        required=True,
    )
    with st.container(horizontal=True):
        if st.button("Lưu", type="primary", icon=":material/save:"):
            try:
                update_task(task.id, text=text, note=note, session=session)
            except ValueError as error:
                st.warning(str(error))
                return
            clear_task_dialogs()
            st.toast("Đã lưu việc.", icon=":material/check_circle:")
            st.rerun()
        if st.button("Hủy", type="tertiary"):
            clear_task_dialogs()
            st.rerun()


@st.dialog("Xóa việc", icon=":material/delete:", on_dismiss=clear_task_dialogs)
def delete_task_dialog(task: Task) -> None:
    st.write(f"Xóa **{escape_markdown(task.text)}** khỏi {weekday_full(date.fromisoformat(task.date))} {format_date(date.fromisoformat(task.date))}?")
    with st.container(horizontal=True):
        if st.button("Xóa", type="primary", icon=":material/delete:"):
            delete_task(task.id)
            clear_task_dialogs()
            st.toast("Đã xóa việc.", icon=":material/delete:")
            st.rerun()
        if st.button("Giữ lại", type="tertiary"):
            clear_task_dialogs()
            st.rerun()


def render_open_dialog() -> None:
    from utils.storage import get_task

    edit_id = st.session_state.get("edit_task_id")
    delete_id = st.session_state.get("delete_task_id")
    if edit_id:
        task = get_task(edit_id)
        if task is None:
            clear_task_dialogs()
        else:
            edit_task_dialog(task)
            return
    if delete_id:
        task = get_task(delete_id)
        if task is None:
            clear_task_dialogs()
        else:
            delete_task_dialog(task)


def render_task_row(task: Task, *, key_prefix: str = "") -> None:
    label = escape_markdown(task.text)
    if task.done:
        label = f"~~{label}~~"
    widget_key = f"{key_prefix}done_{task.id}"
    with st.container(horizontal=True, vertical_alignment="center"):
        st.checkbox(
            label,
            value=task.done,
            key=widget_key,
            on_change=_toggle_done,
            args=(task.id, widget_key),
            width="stretch",
        )
        st.button(
            "Sửa",
            icon=":material/edit:",
            type="tertiary",
            key=f"{key_prefix}edit_{task.id}",
            help="Sửa nội dung, ghi chú hoặc buổi",
            on_click=open_edit_dialog,
            args=(task.id,),
        )
        st.button(
            "Xóa",
            icon=":material/delete:",
            type="tertiary",
            key=f"{key_prefix}del_{task.id}",
            help="Xóa việc này",
            on_click=open_delete_dialog,
            args=(task.id,),
        )
    note_key = f"{key_prefix}task_note_{task.id}"
    if note_key not in st.session_state:
        st.session_state[note_key] = task.note
    st.text_area(
        "Ghi chú việc",
        placeholder="Ghi chú cho việc này…",
        height=70,
        key=note_key,
        on_change=_save_task_note,
        args=(task.id, note_key),
        help="Tự lưu khi bạn rời ô ghi chú.",
    )

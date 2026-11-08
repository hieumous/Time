from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from utils.calendar import VN_TZ, iso

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "planner.json"
_LOCK = threading.Lock()


@dataclass
class Task:
    id: str
    date: str
    session: str
    text: str
    done: bool = False
    note: str = ""
    created_at: str = ""
    done_at: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Task:
        return cls(
            id=str(payload["id"]),
            date=str(payload["date"]),
            session=str(payload["session"]),
            text=str(payload.get("text", "")),
            done=bool(payload.get("done", False)),
            note=str(payload.get("note", "")),
            created_at=str(payload.get("created_at", "")),
            done_at=payload.get("done_at"),
        )


def _now_iso() -> str:
    return datetime.now(VN_TZ).replace(microsecond=0).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"tasks": [], "session_notes": {}}


def _read() -> dict[str, Any]:
    if not DATA_PATH.exists():
        return _empty_store()
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_store()
    if not isinstance(payload, dict):
        return _empty_store()
    payload.setdefault("tasks", [])
    payload.setdefault("session_notes", {})
    return payload


def _write(payload: dict[str, Any]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp_path = DATA_PATH.with_suffix(".tmp")
    tmp_path.write_text(encoded, encoding="utf-8")
    tmp_path.replace(DATA_PATH)


def load_tasks() -> list[Task]:
    with _LOCK:
        payload = _read()
    return [Task.from_dict(item) for item in payload["tasks"] if isinstance(item, dict)]


def get_task(task_id: str) -> Task | None:
    for task in load_tasks():
        if task.id == task_id:
            return task
    return None


def tasks_for(day: date, session: str | None = None) -> list[Task]:
    day_key = iso(day)
    matched = [task for task in load_tasks() if task.date == day_key]
    if session is not None:
        matched = [task for task in matched if task.session == session]
    return matched


def tasks_in_range(start: date, end: date) -> list[Task]:
    start_key = iso(start)
    end_key = iso(end)
    return [task for task in load_tasks() if start_key <= task.date <= end_key]


def add_task(day: date, session: str, text: str, note: str = "") -> Task:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Nội dung việc không được trống.")
    task = Task(
        id=str(uuid.uuid4()),
        date=iso(day),
        session=session,
        text=cleaned,
        note=note.strip(),
        created_at=_now_iso(),
    )
    with _LOCK:
        payload = _read()
        payload["tasks"].append(asdict(task))
        _write(payload)
    return task


def update_task(
    task_id: str,
    *,
    text: str | None = None,
    note: str | None = None,
    session: str | None = None,
    day: date | None = None,
) -> Task | None:
    with _LOCK:
        payload = _read()
        for item in payload["tasks"]:
            if item.get("id") != task_id:
                continue
            if text is not None:
                cleaned = text.strip()
                if not cleaned:
                    raise ValueError("Nội dung việc không được trống.")
                item["text"] = cleaned
            if note is not None:
                item["note"] = note.strip()
            if session is not None:
                item["session"] = session
            if day is not None:
                item["date"] = iso(day)
            _write(payload)
            return Task.from_dict(item)
    return None


def set_done(task_id: str, done: bool) -> Task | None:
    with _LOCK:
        payload = _read()
        for item in payload["tasks"]:
            if item.get("id") != task_id:
                continue
            item["done"] = done
            item["done_at"] = _now_iso() if done else None
            _write(payload)
            return Task.from_dict(item)
    return None


def delete_task(task_id: str) -> bool:
    with _LOCK:
        payload = _read()
        before = len(payload["tasks"])
        payload["tasks"] = [item for item in payload["tasks"] if item.get("id") != task_id]
        if len(payload["tasks"]) == before:
            return False
        _write(payload)
        return True


def session_note_key(day: date, session: str) -> str:
    return f"{iso(day)}:{session}"


def get_session_note(day: date, session: str) -> str:
    with _LOCK:
        payload = _read()
    notes = payload.get("session_notes", {})
    return str(notes.get(session_note_key(day, session), ""))


def save_session_note(day: date, session: str, note: str) -> None:
    with _LOCK:
        payload = _read()
        notes = payload.setdefault("session_notes", {})
        key = session_note_key(day, session)
        cleaned = note.strip()
        if cleaned:
            notes[key] = cleaned
        else:
            notes.pop(key, None)
        _write(payload)


def load_session_notes() -> dict[str, str]:
    """Return every saved session note, keyed by YYYY-MM-DD:session."""
    with _LOCK:
        payload = _read()
    notes = payload.get("session_notes", {})
    if not isinstance(notes, dict):
        return {}
    return {str(key): str(value) for key, value in notes.items()}


def parse_session_note_key(key: str) -> tuple[date, str] | None:
    day_text, separator, session_id = key.partition(":")
    if not separator or session_id not in {"morning", "afternoon", "evening"}:
        return None
    try:
        return date.fromisoformat(day_text), session_id
    except ValueError:
        return None

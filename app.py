from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from utils.calendar import monday_of, week_dates
from utils.export import EXCEL_MIME, build_excel_bytes, excel_filename
from utils.storage import Task

PAGE = Path(__file__).resolve().parent / "web" / "index.html"
SESSIONS = {"morning", "afternoon", "evening"}

app = FastAPI(title="Quản lý thời gian")


class TaskIn(BaseModel):
    id: str = ""
    date: str
    session: str
    text: str = ""
    done: bool = False
    note: str = ""
    created_at: str = ""
    done_at: str | None = None


class ExportIn(BaseModel):
    tasks: list[TaskIn] = Field(default_factory=list)
    notes: dict[str, str] = Field(default_factory=dict)
    week_start: str | None = None


@app.get("/")
def home() -> FileResponse:
    return FileResponse(PAGE, media_type="text/html; charset=utf-8")


@app.post("/api/export")
def export_excel(body: ExportIn) -> Response:
    tasks: list[Task] = []
    for item in body.tasks:
        if item.session not in SESSIONS:
            raise HTTPException(status_code=400, detail="Buổi không hợp lệ.")
        try:
            date.fromisoformat(item.date)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Ngày không hợp lệ.") from error
        text = item.text.strip()
        if not text:
            continue
        tasks.append(
            Task(
                id=item.id or text,
                date=item.date,
                session=item.session,
                text=text,
                done=item.done,
                note=item.note.strip(),
                created_at=item.created_at,
                done_at=item.done_at,
            )
        )

    week_days = None
    if body.week_start:
        try:
            start = date.fromisoformat(body.week_start)
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Tuần không hợp lệ.") from error
        week_days = week_dates(monday_of(start))

    payload = build_excel_bytes(tasks, week_days=week_days, notes=body.notes)
    return Response(
        content=payload,
        media_type=EXCEL_MIME,
        headers={"Content-Disposition": f'attachment; filename="{excel_filename()}"'},
    )

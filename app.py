import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import psycopg
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field

DATABASE_URL = os.environ["DATABASE_URL"]
INDEX = Path(__file__).with_name("index.html")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service.name": "tasks",
            "logger": record.name,
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
log = logging.getLogger("tasks")

app = FastAPI()


def log_access(request, status, start, exc_info=False):
    level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
    fields = {
        "http.method": request.method,
        "url.path": request.url.path,
        "http.status_code": status,
        "duration_ms": round((time.perf_counter() - start) * 1000),
    }
    log.log(level, "%s %s %s", request.method, request.url.path, status, exc_info=exc_info, extra={"fields": fields})


@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log_access(request, 500, start, exc_info=True)
        raise
    log_access(request, response.status_code, start)
    return response


class TaskIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    status: Literal["todo", "doing", "done"] = "todo"


def query(sql, params=()):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as db:
        return db.execute(sql, params).fetchall()


def one(sql, params):
    try:
        rows = query(sql, params)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Такая задача уже есть")
    if not rows:
        raise HTTPException(404, "Задача не найдена")
    return rows[0]


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX)


@app.get("/api/tasks")
def list_tasks():
    return query("SELECT * FROM tasks ORDER BY id")


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskIn):
    return one("INSERT INTO tasks (title, status) VALUES (%s, %s) RETURNING *", (task.title, task.status))


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    return one("SELECT * FROM tasks WHERE id = %s", (task_id,))


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn):
    return one("UPDATE tasks SET title = %s, status = %s WHERE id = %s RETURNING *", (task.title, task.status, task_id))


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    one("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))


if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")), log_config=None, access_log=False)

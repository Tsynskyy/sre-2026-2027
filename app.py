import os
from pathlib import Path

import psycopg
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field

DATABASE_URL = os.environ["DATABASE_URL"]
INDEX = Path(__file__).with_name("index.html")

app = FastAPI(title="Задачи")


class TaskIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


def query(sql, params=()):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as db:
        return db.execute(sql, params).fetchall()


def one(sql, params):
    rows = query(sql, params)
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
    return one("INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *", (task.title, task.done))


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    return one("SELECT * FROM tasks WHERE id = %s", (task_id,))


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn):
    return one("UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *", (task.title, task.done, task_id))


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    one("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))


if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")))

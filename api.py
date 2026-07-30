from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Any, Generator, Optional
import db

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    db.init_db()
    yield

app = FastAPI(lifespan=lifespan)

SEED = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False},
]

data = [dict(task) for task in SEED]

@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/", "/health", "/tasks", "/tasks/{task_id}", "/stats", "/reset"] }


@app.get("/tasks")
async def get_tasks(done: Optional[bool] = None, search: Optional[str] = None) -> list[dict[Any, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM task WHERE 1=1"
    params = []

    if done is not None:
        query += " AND done = ?"
        params.append(int(done))
    if search is not None:
        query += " AND LOWER(title) LIKE ?"
        params.append(f"%{search.lower()}%")

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


@app.get("/tasks/{task_id}")
async def get_task(task_id: int) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    task = dict(row) if row else None
    if task:
        return JSONResponse(status_code=200, content=task)
    return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })


@app.get("/stats")
async def get_stats():
    total = len(data)
    done = sum(1 for task in data if task["done"])
    return { "total": total, "done": done, "open": total - done }


@app.post("/reset")
async def reset_tasks():
    data[:] = [dict(task) for task in SEED]
    return JSONResponse(status_code=200, content={ "message": "Tasks reset to seed data", "count": len(data) })


@app.get("/health")
async def health():
    return { "status": "ok" }


@app.post("/tasks")
async def create_task(task: dict):
    conn = db.get_connection()
    cursor = conn.cursor()

    if task.get("title") is None:
        return JSONResponse(status_code=400, content={ "error": "Title is required" })
    cursor.execute(
        "INSERT INTO task (title, done) VALUES (?, ?)",
        (task["title"], False))

    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={ "message": "Task created successfully" })


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: dict):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    existing_task = dict(row) if row else None
    if existing_task is None:
        return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })
    if task.get("title") is None and task.get("done") is None:
        return JSONResponse(status_code=400, content={ "error": "Title and done status are required" })

    cursor.execute(
        "UPDATE task SET title = COALESCE(?, title), done = COALESCE(?, done) WHERE id = ?",
        (task.get("title"), task.get("done"), task_id)
    )
    conn.commit()
    conn.close()
    return JSONResponse(status_code=200, content={ "message": f"Task {task_id} updated successfully" })


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task WHERE id = ?", (task_id,))
    row = cursor.fetchone()


    existing_task = dict(row) if row else None
    if existing_task is None:
        return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })
    cursor.execute("DELETE FROM task WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return JSONResponse(status_code=204, content={ "message": f"Task {task_id} deleted successfully" })

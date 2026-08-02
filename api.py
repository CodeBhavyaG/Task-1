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


@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/", "/health", "/tasks", "/tasks/{task_id}", "/stats", "/reset"] }


@app.get("/tasks")
async def get_tasks(done: Optional[bool] = None, search: Optional[str] = None) -> list[dict[Any, Any]]:
    conn = db.get_connection()
    cursor = conn.cursor()

    if not conn:
        return JSONResponse(status_code=500, content={ "error": "Database connection failed" })

    query = "SELECT * FROM tasks WHERE 1=1"

    if done is not None:
        query += f" AND done = {done}"
    if search is not None:
        query += f" AND LOWER(title) LIKE '%{search.lower()}%'"

    cursor.execute(query)
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
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM task")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM task WHERE done = 1")
    done = cursor.fetchone()[0]
    conn.close()
    return { "total": total, "done": done, "open": total - done }


@app.post("/reset")
async def reset_tasks():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM task")
    for task in SEED:
        cursor.execute(
            "INSERT INTO task (id, title, done) VALUES (?, ?, ?)",
            (task["id"], task["title"], task["done"])
        )
    conn.commit()
    conn.close()
    return JSONResponse(status_code=200, content={ "message": "Tasks reset to seed data", "count": len(SEED) })


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
